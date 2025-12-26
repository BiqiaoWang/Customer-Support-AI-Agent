# build_index_online_v2.py
"""
Folder -> (Markdown header split) -> (size split) -> Azure embeddings -> Qdrant upsert

Metadata minimal in payload:
- p: policy id (doc_id)
- v: version
- c: card id (e.g., RE-A1)

Run:
  python build_index_online_v2.py
"""

import os
import re
import uuid
from pathlib import Path

from langchain_text_splitters import MarkdownHeaderTextSplitter, RecursiveCharacterTextSplitter
from langchain_openai import AzureOpenAIEmbeddings
from qdrant_client import QdrantClient, models


# ====== Config (match your build_index_online.py) ======
POLICY_DIR = "/Users/shawn/Desktop/internship/UC-25-Summer-DATA601-AI-Agents/UC-25-Summer-DATA601-AI-Agents/RAG_policy/Policy_sum"

QDRANT_URL = "https://935b80de-2d8b-4e02-930b-7c2c068dcb00.us-east4-0.gcp.cloud.qdrant.io:6333"
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")

COLLECTION_NAME = "support_kb_collection"
RECREATE_COLLECTION = True

AZURE_OPENAI_ENDPOINT = os.getenv(
    "AZURE_OPENAI_ENDPOINT",
    "https://student-openai-uc.openai.azure.com/",
)
AZURE_OPENAI_API_KEY = os.getenv("AZURE_OPENAI_API_KEY")
AZURE_OPENAI_API_VERSION = os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-01")
AZURE_OPENAI_EMBED_DEPLOYMENT = os.getenv("AZURE_OPENAI_EMBED_DEPLOYMENT", "text-embedding-3-small")

CHUNK_SIZE = 1200
CHUNK_OVERLAP = 200
UPSERT_BATCH_SIZE = 128
# ================================================

# Matches RE-A1 / IT-D1 / BP-B1 / SEC-A2 ...
CARD_RE = re.compile(r"^([A-Z]{2,6}-[A-Z]\d+)\b")


def parse_front_matter(md: str):
    """
    Supports 2 formats:

    A) YAML-like:
    ---
    doc_id: returns-exchanges-policy
    title: Returns & Exchanges Policy
    version: 2025-12-23
    ---

    B) Your one-line tokens:
    --- docid returns-exchanges-policy title Returns & Exchanges Policy version 2025-12-23 ---
    """
    if not md.startswith("---"):
        return {}, md

    parts = md.split("---", 2)
    if len(parts) < 3:
        return {}, md

    header = parts[1].strip()
    body = parts[2].lstrip("\n")
    meta = {}

    # Case A: YAML-like
    if ":" in header:
        for line in header.splitlines():
            if ":" in line:
                k, v = line.split(":", 1)
                meta[k.strip()] = v.strip()
        # normalize keys if user used docid
        if "docid" in meta and "doc_id" not in meta:
            meta["doc_id"] = meta["docid"]
        return meta, body

    # Case B: one-line tokens
    m_docid = re.search(r"\bdocid\s+([^\s]+)", header)
    m_version = re.search(r"\bversion\s+([0-9]{4}-[0-9]{2}-[0-9]{2})\b", header)
    m_title = re.search(
        r"\btitle\s+(.*?)\s+version\s+[0-9]{4}-[0-9]{2}-[0-9]{2}\b",
        header,
    )

    if m_docid:
        meta["doc_id"] = m_docid.group(1)
    if m_version:
        meta["version"] = m_version.group(1)
    if m_title:
        meta["title"] = m_title.group(1).strip()

    return meta, body


def make_point_id(p: str, c: str, i: int) -> str:
    # Deterministic ID so reruns overwrite points (when RECREATE_COLLECTION=False)
    return str(uuid.uuid5(uuid.NAMESPACE_URL, f"{p}::{c}::{i}"))


def batched(iterable, n: int):
    buf = []
    for x in iterable:
        buf.append(x)
        if len(buf) >= n:
            yield buf
            buf = []
    if buf:
        yield buf


def main():
    # 0) validate env
    if not AZURE_OPENAI_API_KEY or not AZURE_OPENAI_ENDPOINT or not AZURE_OPENAI_API_VERSION:
        raise RuntimeError(
            "Azure OpenAI configuration is incomplete. "
            "Please set AZURE_OPENAI_API_KEY / AZURE_OPENAI_ENDPOINT / AZURE_OPENAI_API_VERSION."
        )

    if not QDRANT_API_KEY:
        raise RuntimeError("Qdrant API key is missing. Please set QDRANT_API_KEY in your environment.")

    policy_dir = Path(POLICY_DIR)
    if not policy_dir.exists():
        raise RuntimeError(f"POLICY_DIR not found: {POLICY_DIR}")

    md_files = sorted(policy_dir.glob("*.md"))
    print("Found md files:", len(md_files))
    if not md_files:
        raise RuntimeError(f"No .md files found under: {POLICY_DIR}")

    # 1) split
    md_header_splitter = MarkdownHeaderTextSplitter(
        headers_to_split_on=[("#", "h1"), ("##", "h2"), ("###", "h3")],
        strip_headers=False,
    )
    sub_splitter = RecursiveCharacterTextSplitter(chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP)

    chunks = []  # list of (text, meta_pvc, local_i)
    for fp in md_files:
        md = fp.read_text(encoding="utf-8")
        fm, body = parse_front_matter(md)

        header_docs = md_header_splitter.split_text(body)
        small_docs = sub_splitter.split_documents(header_docs)

        p_val = fm.get("doc_id", fp.stem)
        v_val = fm.get("version", "")

        for local_i, d in enumerate(small_docs):
            h3 = (d.metadata.get("h3") or "").strip()
            card_id = ""
            m = CARD_RE.match(h3)
            if m:
                card_id = m.group(1)

            meta = {"p": p_val, "v": v_val, "c": card_id}
            chunks.append((d.page_content, meta, local_i))

    print(f"Loaded & split: {len(chunks)} chunks")

    # 2) embeddings
    embeddings = AzureOpenAIEmbeddings(
        model=AZURE_OPENAI_EMBED_DEPLOYMENT,
        azure_endpoint=AZURE_OPENAI_ENDPOINT,
        api_key=AZURE_OPENAI_API_KEY,
        openai_api_version=AZURE_OPENAI_API_VERSION,
    )

    vector_size = len(embeddings.embed_query("test"))
    print("Vector size:", vector_size)

    # 3) qdrant connect + create
    client = QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY)

    if RECREATE_COLLECTION:
        try:
            client.delete_collection(COLLECTION_NAME)
        except Exception:
            pass

        client.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=models.VectorParams(size=vector_size, distance=models.Distance.COSINE),
        )
        print("Created collection:", COLLECTION_NAME)
    else:
        # create if missing
        try:
            client.get_collection(COLLECTION_NAME)
        except Exception:
            client.create_collection(
                collection_name=COLLECTION_NAME,
                vectors_config=models.VectorParams(size=vector_size, distance=models.Distance.COSINE),
            )
            print("Created collection:", COLLECTION_NAME)

    # 4) upsert in batches
    total = 0
    for batch in batched(chunks, UPSERT_BATCH_SIZE):
        texts = [t for (t, _, _) in batch]
        vecs = embeddings.embed_documents(texts)

        points = []
        for (text, meta, local_i), vec in zip(batch, vecs):
            pid = make_point_id(meta.get("p", ""), meta.get("c", ""), local_i)
            payload = {"text": text, **meta}
            points.append(models.PointStruct(id=pid, vector=vec, payload=payload))

        client.upsert(collection_name=COLLECTION_NAME, points=points)
        total += len(points)

    print("Upserted points:", total)
    print("Done.")


if __name__ == "__main__":
    main()
