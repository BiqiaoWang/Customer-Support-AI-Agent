import os
import time
import json
import re
import pandas as pd
from tqdm import tqdm
from groq import Groq, APIStatusError

# In the system, setx GROQ_API_KEY
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

MODEL = "llama-3.1-8b-instant"
INPUT_CSV = "combined_tickets_clean_text.csv"
OUTPUT_CSV = "combined_tickets_clean_with_sentiment.csv"

# 每批多少条，根据之前的报错，20 条比较安全
BATCH_SIZE = 20
MAX_BATCH_RETRIES = 5      # 一整批失败时的最大重试次数
MAX_SINGLE_RETRIES = 3     # 单条重试次数
ALLOWED_LABELS = {"positive", "neutral", "negative"}


# ----------- 通用：带重试的 Groq 调用 ------------- #
def parse_wait_seconds_from_msg(msg: str, default: int = 60) -> int:
    """
    从 Groq 的报错信息里解析 'try again in 3m24s' 这样的提示。
    解析失败就用 default。
    """
    m = re.search(r'(\d+)m(\d+)s', msg)
    if m:
        return int(m.group(1)) * 60 + int(m.group(2))
    m2 = re.search(r'(\d+)s', msg)
    if m2:
        return int(m2.group(1))
    return default


def call_groq_with_retry(**kwargs):
    backoff = 10
    for attempt in range(1, MAX_BATCH_RETRIES + 1):
        try:
            return client.chat.completions.create(**kwargs)
        except APIStatusError as e:
            msg = str(e)
            # 限流 / token 限制之类的错误，自动等待后重试
            if "rate_limit_exceeded" in msg or "TPM" in msg or "TPD" in msg:
                wait_s = parse_wait_seconds_from_msg(msg, default=60)
                print(f"\n⚠ Groq 限流/额度限制，第 {attempt} 次重试，等待 {wait_s} 秒…")
                time.sleep(wait_s)
                backoff = min(backoff * 2, 600)
                continue
            else:
                print("\n❌ Groq APIStatusError（非限流类），停止：", msg)
                raise
        except Exception as e:
            print(f"\n⚠ 调用 Groq 出错：{e}，第 {attempt} 次重试，等待 {backoff} 秒…")
            time.sleep(backoff)
            backoff = min(backoff * 2, 600)
    raise RuntimeError("多次重试 Groq 仍失败，终止本批。")


# ----------- 批量分类（主力） ------------- #
def classify_batch(texts):
    """
    一次性给模型一批文本，要求返回一个 JSON 数组：
    ["negative", "positive", "neutral", ...]
    """
    numbered = "\n".join([f"{i+1}. {t}" for i, t in enumerate(texts)])

    prompt = f"""
Classify the sentiment of each ticket description as "positive", "neutral", or "negative".

Return ONLY a JSON array of strings, in order, like:
["negative","neutral","positive"]

Ticket descriptions:
{numbered}
"""

    resp = call_groq_with_retry(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}],
        max_tokens=1000,
        temperature=0,
    )

    content = resp.choices[0].message.content.strip()

    # 期望 content 就是一个 JSON 数组
    try:
        labels = json.loads(content)
    except json.JSONDecodeError:
        print("⚠ JSON 解析失败，模型输出：")
        print(content)
        # 兜底，本批全部 unknown
        return ["unknown"] * len(texts)

    if not isinstance(labels, list):
        print("⚠ 模型输出不是列表，本批标记为 unknown：")
        print(content)
        return ["unknown"] * len(texts)

    if len(labels) != len(texts):
        print(f"⚠ 标签数量不等于输入数量（labels={len(labels)}, texts={len(texts)}），本批标记为 unknown")
        return ["unknown"] * len(texts)

    # 返回原始标签（后面再做合法性校验）
    return labels


# ----------- 单条分类（用于补救 unknown 或非法标签） ------------- #
def classify_single(text: str) -> str:
    prompt = f"""
Classify the sentiment of the following ticket description as "positive", "neutral", or "negative".
Return ONLY one word.

Description: {text}
"""
    for attempt in range(1, MAX_SINGLE_RETRIES + 1):
        try:
            resp = call_groq_with_retry(
                model=MODEL,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=5,
                temperature=0,
            )
            label = resp.choices[0].message.content.strip().lower()
            label = label.replace(".", "").strip('" ').strip()
            if label in ALLOWED_LABELS:
                return label
        except Exception as e:
            print(f"⚠ 单条重试出错（第 {attempt} 次）：{e}")
            time.sleep(3 * attempt)

    return "unknown"


# ----------- 主流程：断点续跑 + 批处理 ------------- #
def main():
    # 读原始数据
    df = pd.read_csv(INPUT_CSV)
    total = len(df)

    # 如果输出文件存在，则从已有进度恢复
    if os.path.exists(OUTPUT_CSV):
        out_df = pd.read_csv(OUTPUT_CSV)
        # 同步已有 sentiment 到 df
        if "sentiment" in out_df.columns:
            df["sentiment"] = out_df["sentiment"]
        else:
            df["sentiment"] = ""
        # 已完成的行：sentiment 非空且不是空字符串
        done_mask = df["sentiment"].notna() & (df["sentiment"].astype(str) != "")
        already_done = done_mask.sum()
        print(f"🔁 检测到已有进度：已完成 {already_done}/{total} 条")
    else:
        df["sentiment"] = ""
        already_done = 0
        print("🆕 首次运行，从头开始")

    print(f"📊 总共有 {total} 条工单，批大小 = {BATCH_SIZE}")

    # 主循环：从 already_done 开始按批处理
    for start in tqdm(range(already_done, total, BATCH_SIZE)):
        end = min(start + BATCH_SIZE, total)
        batch_df = df.iloc[start:end]
        texts = batch_df["ticket_description"].astype(str).tolist()

        # 1. 批量获取初始标签
        raw_labels = classify_batch(texts)

        # 2. 校验标签合法性，不合法的用单条接口重试
        fixed_labels = []
        for text, label in zip(texts, raw_labels):
            if label is None:
                label = ""
            norm = str(label).strip().lower()
            norm = norm.replace(".", "").strip('" ').strip()

            if norm not in ALLOWED_LABELS:
                # 对非法标签 / unknown 进行单条重试
                norm = classify_single(text)

            fixed_labels.append(norm)

        # 3. 写回到 df 对应行
        df.loc[start:end-1, "sentiment"] = fixed_labels

        # 4. 每批保存一次完整进度
        cols = ["ticket_type", "ticket_description", "priority", "sentiment"]
        df[cols].to_csv(OUTPUT_CSV, index=False)

        # 轻微 sleep，避免触发频率限制
        time.sleep(0.3)

    print(f"🎉 全部完成！结果已保存到：{OUTPUT_CSV}")


if __name__ == "__main__":
    main()
