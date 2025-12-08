import pandas as pd
import re
from sentence_transformers import SentenceTransformer
import numpy as np
import hdbscan
import json

# ========= Step 1: 读取清洗后的 CSV =========
csv_path = "/Users/shawn/Desktop/internship/UC-25-Summer-DATA601-AI-Agents/UC-25-Summer-DATA601-AI-Agents/RAG_policy/ Billing and Payments cleaned.csv"

text_col = "cleaned_answer"   # 你的表头

df = pd.read_csv(csv_path)
texts = df[text_col].dropna().astype(str).tolist()

# ========= Step 2: 简单按句子再切一刀（可选） =========
def split_to_sentences(text):
    # 粗切：按 . ? ! 换行等分句，可按需要改
    parts = re.split(r'[\.!?]\s+|\n+', text)
    return [p.strip() for p in parts if len(p.strip()) >= 10]

sentences = []
for t in texts:
    sents = split_to_sentences(t)
    sentences.extend(sents)

# 去重
sentences = list(dict.fromkeys(sentences))
print("句子数量:", len(sentences))

# ========= Step 3: Sentence-BERT 向量化 =========
model = SentenceTransformer("all-MiniLM-L6-v2")
embeddings = model.encode(sentences, batch_size=32, show_progress_bar=True)
embeddings = np.asarray(embeddings)

# ========= Step 4: HDBSCAN 聚类 =========
min_cluster_size = 10      # ★ 可调1：簇里最少句子数
min_samples = None         # ★ 可调2：噪声敏感度（先用 None）
metric = "euclidean"

clusterer = hdbscan.HDBSCAN(
    min_cluster_size=min_cluster_size,
    min_samples=min_samples,
    metric=metric,
    cluster_selection_method='eom'
)

cluster_labels = clusterer.fit_predict(embeddings)
print("簇数量（不含噪声）:", len(set(cluster_labels)) - (1 if -1 in cluster_labels else 0))

# ========= Step 5: 组装簇（label -> 句子列表） =========
cluster_to_sentences = {}
for sent, label in zip(sentences, cluster_labels):
    if label == -1:
        continue  # 丢掉噪声
    cluster_to_sentences.setdefault(label, []).append(sent)

# 简单打印前几个簇看看
for cid, sents in list(cluster_to_sentences.items())[:5]:
    print(f"\n=== Cluster {cid} （样本数 {len(sents)}）===")
    for s in sents[:5]:
        print(" -", s)

# ========= Step 6: 只导出 JSON =========
clusters_json = []
for cid, sents in cluster_to_sentences.items():
    clusters_json.append({
        "cluster_id": int(cid),
        "sentences": sents
    })

with open("billing_clusters.json", "w", encoding="utf-8") as f:
    json.dump(clusters_json, f, ensure_ascii=False, indent=2)
