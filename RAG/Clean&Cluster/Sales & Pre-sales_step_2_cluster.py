import pandas as pd
import re
from sentence_transformers import SentenceTransformer
import numpy as np
import hdbscan
import json


# ========= Step 1: Read cleaned CSV =========
csv_path = "/Users/shawn/Desktop/internship/UC-25-Summer-DATA601-AI-Agents/UC-25-Summer-DATA601-AI-Agents/RAG_policy/Customer-Pre-Sales-Engagement_cleaned.csv"  # Pre-Sales cleaned file

text_col = "cleaned_answer"   # Your column header

df = pd.read_csv(csv_path)
texts = df[text_col].dropna().astype(str).tolist()

print(f"Loaded {len(texts)} texts from CSV")

# ========= Step 2: Split into sentences (optional refinement) =========
def split_to_sentences(text):
    # Rough split: by . ? ! and newlines, keep sentences >= 10 chars
    parts = re.split(r'[\.!?]\s+|\n+', text)
    return [p.strip() for p in parts if len(p.strip()) >= 10]

sentences = []
for t in texts:
    sents = split_to_sentences(t)
    sentences.extend(sents)

# Deduplicate
sentences = list(dict.fromkeys(sentences))
print("Total unique sentences:", len(sentences))


# ========= Step 3: Sentence-BERT embedding =========
model = SentenceTransformer("all-MiniLM-L6-v2")
embeddings = model.encode(sentences, batch_size=32, show_progress_bar=True)
embeddings = np.asarray(embeddings)


# ========= Step 4: HDBSCAN clustering =========
min_cluster_size = 8       # Slightly smaller for Pre-Sales (more fragmented topics)
min_samples = None         # Automatic noise detection
metric = "euclidean"

clusterer = hdbscan.HDBSCAN(
    min_cluster_size=min_cluster_size,
    min_samples=min_samples,
    metric=metric,
    cluster_selection_method='eom'
)

cluster_labels = clusterer.fit_predict(embeddings)
n_clusters = len(set(cluster_labels)) - (1 if -1 in cluster_labels else 0)
n_noise = list(cluster_labels).count(-1)
print(f"Clusters (excluding noise): {n_clusters}")
print(f"Noise points: {n_noise}")


# ========= Step 5: Assemble clusters (label -> sentence list) =========
cluster_to_sentences = {}
for sent, label in zip(sentences, cluster_labels):
    if label == -1:
        continue  # Discard noise
    cluster_to_sentences.setdefault(label, []).append(sent)

print(f"Final clusters with sentences: {len(cluster_to_sentences)}")

# Print sample clusters (Pre-Sales topics)
for cid, sents in list(cluster_to_sentences.items())[:5]:
    print(f"\n=== Cluster {cid} (size: {len(sents)}) ===")
    for s in sents[:3]:  # Show top 3
        print(" -", s)


# ========= Step 6: Export JSON =========
clusters_json = []
for cid, sents in sorted(cluster_to_sentences.items(), key=lambda x: x[0]):
    clusters_json.append({
        "cluster_id": int(cid),
        "sentences": sents,
        "size": len(sents)
    })

output_file = "pre_sales_clusters.json"
with open(output_file, "w", encoding="utf-8") as f:
    json.dump(clusters_json, f, ensure_ascii=False, indent=2)

print(f"\n✅ Exported {len(clusters_json)} clusters to: {output_file}")
print(f"📊 Stats: {sum(c['size'] for c in clusters_json)} sentences across {len(clusters_json)} clusters")
