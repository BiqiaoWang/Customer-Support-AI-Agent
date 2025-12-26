import os
import time
import re

import pandas as pd
from tqdm import tqdm
from groq import Groq, APIStatusError

GROQ_MODEL = "llama-3.1-8b-instant"
OPENAI_MODEL = "openai/gpt-oss-20b"

INPUT_CSV = "data/gold_set_labeled.csv"
OUTPUT_CSV = INPUT_CSV

GROQ_COL = "llama-3.1-8b-instant"
OPENAI_COL = "gpt-oss-20b"

MAX_API_RETRIES = 5
SAVE_EVERY = 10
SLEEP_SECONDS = 0.2
ALLOWED_LABELS = {"0", "1"}


def parse_wait_seconds_from_msg(msg: str, default: int = 60) -> int:
    m = re.search(r"(\d+)m(\d+)s", msg)
    if m:
        return int(m.group(1)) * 60 + int(m.group(2))
    m2 = re.search(r"(\d+)s", msg)
    if m2:
        return int(m2.group(1))
    return default


def build_prompt(text: str) -> str:
    return f"""Classify the sentiment of the ticket description as negative or non-negative.
Return ONLY 1 or 0.
Negative => 1
Non-negative (neutral or positive) => 0

Ticket description:
{text}"""


def normalize_binary_label(raw):
    if raw is None:
        return None
    label = str(raw).strip()
    if label in ALLOWED_LABELS:
        return label
    return None


def is_valid_label(value) -> bool:
    if value is None or pd.isna(value):
        return False
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        numeric = None
    if numeric in (0.0, 1.0):
        return True
    value_str = str(value).strip()
    return value_str in ALLOWED_LABELS


GROQ_API_KEY = os.getenv("GROQ_API_KEY")
if not GROQ_API_KEY:
    raise RuntimeError("GROQ_API_KEY is not set")
groq_client = Groq(api_key=GROQ_API_KEY)


def call_groq_with_retry(**kwargs):
    backoff = 10
    for attempt in range(1, MAX_API_RETRIES + 1):
        try:
            return groq_client.chat.completions.create(**kwargs)
        except APIStatusError as exc:
            msg = str(exc)
            if "rate_limit_exceeded" in msg or "TPM" in msg or "TPD" in msg:
                wait_s = parse_wait_seconds_from_msg(msg, default=60)
                print(f"Groq rate limit; attempt {attempt}; waiting {wait_s}s")
                time.sleep(wait_s)
                backoff = min(backoff * 2, 600)
                continue
            print(f"Groq APIStatusError: {msg}")
            raise
        except Exception as exc:
            print(f"Groq call failed: {exc}; attempt {attempt}; waiting {backoff}s")
            time.sleep(backoff)
            backoff = min(backoff * 2, 600)
    raise RuntimeError("Groq retries exhausted.")


def classify_binary_groq(text: str) -> str:
    prompt = build_prompt(text)
    while True:
        resp = call_groq_with_retry(
            model=GROQ_MODEL,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=1,
            temperature=0,
        )
        label = normalize_binary_label(resp.choices[0].message.content)
        if label is not None:
            return label
        print("Groq returned invalid label; retrying.")
        time.sleep(1)


def classify_binary_gpt_oss(text: str) -> str:
    prompt = build_prompt(text)
    while True:
        resp = call_groq_with_retry(
            model=OPENAI_MODEL,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=1,
            temperature=0,
        )
        label = normalize_binary_label(resp.choices[0].message.content)
        if label is not None:
            return label
        print("GPT-OSS returned invalid label; retrying.")
        time.sleep(1)


def main():
    df = pd.read_csv(INPUT_CSV)
    if "ticket_description" not in df.columns:
        raise RuntimeError("ticket_description column not found in input CSV")

    for col in (GROQ_COL, OPENAI_COL):
        if col not in df.columns:
            df[col] = pd.NA
        else:
            df[col] = df[col].apply(
                lambda v: pd.NA if not is_valid_label(v) else int(float(v))
            )
        df[col] = df[col].astype("Int64")

    total = len(df)
    save_counter = 0

    for idx, row in tqdm(df.iterrows(), total=total):
        text = row["ticket_description"]
        if pd.isna(text):
            text = ""
        else:
            text = str(text)

        updated = False

        if not is_valid_label(row[GROQ_COL]):
            label = classify_binary_groq(text)
            df.at[idx, GROQ_COL] = int(label)
            updated = True

        if not is_valid_label(row[OPENAI_COL]):
            label = classify_binary_gpt_oss(text)
            df.at[idx, OPENAI_COL] = int(label)
            updated = True

        if updated:
            save_counter += 1
            if save_counter % SAVE_EVERY == 0:
                df.to_csv(OUTPUT_CSV, index=False)
            time.sleep(SLEEP_SECONDS)

    df.to_csv(OUTPUT_CSV, index=False)
    print(f"Done. Results saved to {OUTPUT_CSV}")


if __name__ == "__main__":
    main()
