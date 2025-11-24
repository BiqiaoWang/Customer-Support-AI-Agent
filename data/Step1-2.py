import pandas as pd
import re

# Step1: Combine the datasets
# 读取两个原始表
df1 = pd.read_csv("tickets.csv")      # Table 1
df2 = pd.read_csv("customer_support_tickets.csv") # Table 2

# Table 2：Only keep English language version
df2 = df2[df2["language"] == "en"].copy()

# ------- 统一列名 --------

# 表 1 的列名映射
rename_map_1 = {
    "category": "ticket_type",
    "description": "ticket_description",
    "priority": "priority",
}

df1 = df1.rename(columns=rename_map_1)

# 表 2 的映射
rename_map_2 = {
    "body": "ticket_description",
    "queue": "ticket_type",
    "priority": "priority",
}

df2 = df2.rename(columns=rename_map_2)

# ------- 新的统一 schema --------

final_cols = [
    "ticket_type",
    "ticket_description",
    "priority",
]

# ------- 为每个表补齐缺失列，并保持一致的字段顺序 --------

for col in final_cols:
    if col not in df1.columns:
        df1[col] = pd.NA
    if col not in df2.columns:
        df2[col] = pd.NA

df1 = df1[final_cols]
df2 = df2[final_cols]


# ------- 合并 --------

combined = pd.concat([df1, df2], ignore_index=True)
print("合并完成，总行数：", len(combined))

# Step2: Clean the ticket text


def clean_text(text):
    if pd.isna(text):
        return ""

    text = str(text)

    # 1) 替换真实换行和字面 \n
    text = text.replace("\n", " ").replace("\r", " ")
    text = text.replace("\\n", " ").replace("\\r", " ")

    # 2) 清理 HTML 标签
    text = re.sub(r"<br\s*/?>", " ", text, flags=re.IGNORECASE)
    text = re.sub(r"</?[^>]+>", " ", text)   # 清理其他 HTML 标签，如 <p>、<div>

    # 3) 转小写
    text = text.lower()

    
    # 4) 去掉奇怪字符，只保留字母、数字和少量符号
    text = re.sub(r"[^a-z0-9\s.,!?'\’]", " ", text)

    # 5) 去掉多余空格
    text = re.sub(r"\s+", " ", text).strip()

    return text

# 统一填充空值
combined["ticket_description"] = combined["ticket_description"].fillna("")

# 清洗后直接覆盖原列
combined["ticket_description"] = combined["ticket_description"].astype(str).apply(clean_text)

# =======================
# 导出最终结果
# =======================

combined.to_csv("combined_tickets_clean_text.csv", index=False, encoding="utf-8")
print("文本清洗完成！ticket_description 列已清洗。")