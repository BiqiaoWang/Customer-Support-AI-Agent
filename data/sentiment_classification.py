import pandas as pd
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score

# =========================================================
# Section 1: Stratified Sampling - 抽取 500 条 Gold Set
# （只在“第一次抽样”时运行；之后不需要再跑）
# =========================================================

# 1.1 读取完整工单数据
df = pd.read_csv("combined_tickets_clean_text.csv")

# 1.2 为数据添加唯一 ID
df = df.reset_index().rename(columns={"index": "ticket_id"})

# 1.3 按 ticket_type 分层抽样，目标抽 500 条
N = len(df)
target_n = 500

gold_list = []
selected_ids = []   # 记录选中的 ticket_id，避免后续定位错误

for ttype, group in df.groupby('ticket_type'):
    # 该类型在总体中的占比
    p = len(group) / N
    
    # 该类型应抽数量（按比例）
    k = int(round(target_n * p))
    
    # 至少抽 1 条，防止某个 type 被抽成 0
    k = max(1, k)
    
    # 从该类型中随机抽样（如果该组比 k 还小，就取该组全部）
    sampled = group.sample(n=min(k, len(group)), random_state=42)
    gold_list.append(sampled)
    selected_ids.extend(sampled["ticket_id"].tolist())

# 1.4 汇总所有 type 的样本
gold_df = pd.concat(gold_list, ignore_index=True)

# 1.5 如果数量多于 500 → 随机删到 500
if len(gold_df) > target_n:
    gold_df = gold_df.sample(n=target_n, random_state=42)

# 1.6 如果数量少于 500 → 从剩余没选中的数据里补抽
elif len(gold_df) < target_n:
    remaining = df[~df["ticket_id"].isin(gold_df["ticket_id"])]
    extra = remaining.sample(n=target_n - len(gold_df), random_state=42)
    gold_df = pd.concat([gold_df, extra], ignore_index=True)

# 1.7 保存最终 Gold Set（交给组员人工标注）
gold_df.to_csv("gold_set_stratified_by_ticket_type.csv", index=False)

print("抽样完成，已导出 gold_set_stratified_by_ticket_type.csv （请接下来进行人工标注）")

# =========================================================
# Section 2: 读取“已人工标注”的 Gold Set
# （在人工标注完成之后再运行）
# =========================================================

# 2.1 读取人工标注后的数据
df2 = pd.read_csv("gold_set_labeled.csv")

# 你可以检查一下列是否存在
print(df2.columns)

# 确认一下几列是否在里面：
# - 'ticket_id'
# - 'ticket_description'（工单文本）
# - 'gold_label'（你们手工标注的 0/1）


# =========================================================
# Section 3: 使用 VADER 进行 Lexicon-based Baseline 预测
# =========================================================

# 初始化 VADER 分析器
analyzer = SentimentIntensityAnalyzer()

# 定义二分类函数：Negative vs Non-Negative
def vader_binary(text):
    scores = analyzer.polarity_scores(str(text))  # 转成 str 防止出现 NaN
    compound = scores['compound']
    
    # VADER 阈值：
    # compound <= -0.05 → Negative（1）
    # 否则 → Non-Negative（0）
    if compound <= -0.05:
        return 1
    else:
        return 0

df2["vader_binary"] = df2["ticket_description"].apply(vader_binary)

df2[["ticket_id", "ticket_description", "gold_label", "vader_binary"]].head()

# =========================================================
# Section 4: 计算 Baseline 指标（Accuracy / Precision / Recall / F1）
# =========================================================

y_true = df2["gold_label"]
y_pred = df2["vader_binary"]

print("Recall:", recall_score(y_true, y_pred))
print("Precision:", precision_score(y_true, y_pred))
print("F1 Score:", f1_score(y_true, y_pred))
print("Accuracy:", accuracy_score(y_true, y_pred))