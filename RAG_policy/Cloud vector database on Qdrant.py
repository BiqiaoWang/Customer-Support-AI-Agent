    # build_index_online.py
    """
    One-off indexing script (Azure + Qdrant):
    1. Download Policy_doc.md from GitHub
    2. Split the long document into multiple chunks
    3. Use Azure OpenAI text-embedding-3-small to generate embeddings
    4. Write text + vectors into Qdrant Cloud collection: support_kb_collection
    Run with: python build_index_online.py
    """

    import os
    import requests
    from langchain_text_splitters import RecursiveCharacterTextSplitter
    from langchain_openai import AzureOpenAIEmbeddings
    from qdrant_client import QdrantClient, models

    # ------- Config section -------

    # Remote policy document URL
    POLICY_URL = (
        "https://raw.githubusercontent.com/"
        "UC-25-Summer-DATA601-AI-Agents/UC-25-Summer-DATA601-AI-Agents/"
        "main/RAG_policy/Policy_doc.md"
    )

    # Your Qdrant Cloud URL
    QDRANT_URL = (
        "https://935b80de-2d8b-4e02-930b-7c2c068dcb00.us-east4-0.gcp.cloud.qdrant.io:6333"
    )

    # Your Qdrant API key (read from environment)
    QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")

    # Target collection name
    COLLECTION_NAME = "support_kb_collection"

    # Azure OpenAI config (all from environment or with safe defaults)
    AZURE_OPENAI_ENDPOINT = os.getenv(
        "AZURE_OPENAI_ENDPOINT",
        "https://student-openai-uc.openai.azure.com/",
    )
    AZURE_OPENAI_API_KEY = os.getenv("AZURE_OPENAI_API_KEY")
    AZURE_OPENAI_API_VERSION = os.getenv(
        "AZURE_OPENAI_API_VERSION",
        "2024-02-01",
    )
    AZURE_OPENAI_EMBED_DEPLOYMENT = os.getenv(
        "AZURE_OPENAI_EMBED_DEPLOYMENT",
        "text-embedding-3-small",
    )


    def main():
        # ------- 0. Validate Azure OpenAI config -------
        if not AZURE_OPENAI_API_KEY or not AZURE_OPENAI_ENDPOINT or not AZURE_OPENAI_API_VERSION:
            raise RuntimeError(
                "Azure OpenAI configuration is incomplete. "
                "Please set AZURE_OPENAI_API_KEY / AZURE_OPENAI_ENDPOINT / AZURE_OPENAI_API_VERSION."
            )

        # ------- 1. Download markdown policy from GitHub -------
        resp = requests.get(POLICY_URL, timeout=20)
        resp.raise_for_status()
        policy_text = resp.text
        print(f"Downloaded policy from GitHub, length = {len(policy_text)} characters")

        # ------- 2. Split long document into chunks -------
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=1200,
            chunk_overlap=200,
        )
        docs = splitter.create_documents([policy_text])
        print(f"Created {len(docs)} chunks")

        # ------- 3. Initialize Azure OpenAI embeddings -------
        embeddings = AzureOpenAIEmbeddings(
            model=AZURE_OPENAI_EMBED_DEPLOYMENT,
            azure_endpoint=AZURE_OPENAI_ENDPOINT,
            api_key=AZURE_OPENAI_API_KEY,
            openai_api_version=AZURE_OPENAI_API_VERSION,
        )

        # Compute one test vector to get dimension
        test_vector = embeddings.embed_query("test")
        vector_size = len(test_vector)
        print(f"Embedding vector size = {vector_size}")

        # ------- 4. Connect to Qdrant Cloud -------
        if not QDRANT_API_KEY:
            raise RuntimeError(
                "Qdrant API key is missing. Please set QDRANT_API_KEY in your environment."
            )

        client = QdrantClient(
            url=QDRANT_URL,
            api_key=QDRANT_API_KEY,
        )

        # Delete collection if it exists (ignore errors)
        try:
            client.delete_collection(COLLECTION_NAME)
        except Exception:
            pass

        # Create / recreate collection
        client.recreate_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=models.VectorParams(
                size=vector_size,
                distance=models.Distance.COSINE,
            ),
        )
        print(f"Recreated collection: {COLLECTION_NAME}")

        # ------- 5. Compute embeddings for all chunks and upsert into Qdrant -------
        vectors = []
        payloads = []
        ids = []

        for idx, doc in enumerate(docs):
            vec = embeddings.embed_query(doc.page_content)
            vectors.append(vec)
            payloads.append({"text": doc.page_content})
            ids.append(idx)

        client.upsert(
            collection_name=COLLECTION_NAME,
            points=models.Batch(
                ids=ids,
                vectors=vectors,
                payloads=payloads,
            ),
        )

        print("Finished writing collection:", COLLECTION_NAME)


    if __name__ == "__main__":
        main()
