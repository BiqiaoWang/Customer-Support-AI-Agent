import re
import pandas as pd


# ===== 0. Simple sentence tokenizer =====
def simple_sent_tokenize(text: str):
    """Simple English sentence splitter."""
    if not isinstance(text, str):
        return []
    text = text.replace("\n", " ")
    parts = re.split(r"[.!?]+", text)
    return [p.strip() for p in parts if p.strip()]


# ===== 1. Noise patterns (generic customer-service noise) =====
noise_patterns = [
    # Opening/closing pleasantries
    r"^(thank you|thanks|we appreciate|we apologize|we are sorry|sorry for the inconvenience)\b",
    r"(have a great day|let us know if you have any other questions|we are here to help)",
    # Asking for contact / call
    r"(could you please|please provide|kindly provide|please send|please share)",
    r"(contact us|contact me|reach us|reach me|schedule a call|convenient time|phone call)",
    r"\btelnum\b|\baccnum\b|\bTelNum\b|\bPhone Number\b",
    # Placeholders
    r"<\s*(name|tel_num|acc_num|email|order_num|account number|customer id)\s*>",
    # Generic transition / empathy phrases
    r"(we understand|we recognize the urgency|we look forward to your response|we will be in touch)",
]


# ===== 2a. Returns & Exchanges keywords =====
returns_keywords = [
    "return", "returns", "exchange", "exchanges", "refund", "refunds",
    "replacement", "replace", "rma", "return merchandise authorization",
    "return policy", "exchange policy",
    "within 30 days", "within 14 days", "within 7 days",
    "days of purchase", "days of receiving", "return window",
    "unused", "in their original packaging", "original packaging",
    "original condition", "proof of purchase", "receipt",
    "shipping costs", "shipping cost", "return shipping",
    "prepaid shipping label", "pre-paid shipping label",
    "customer is responsible for", "restocking fee", "cancellation fee",
    "processed within", "business days", "credited to your original payment method",
    "refund will be issued", "refund will be processed",
    "refund to the original payment method", "refund to your credit card",
    "defective", "damaged", "faulty", "incorrect item", "wrong item",
    "incomplete product bundle", "missing items",
    "eligible for return", "eligible for exchange",
    "not eligible for return", "non-refundable",
    "clearance items", "final sale"
]


# ===== 2b. Human Resources / HR keywords =====
hr_keywords = [
    "human resources", "hr department", "hr portal",
    "payroll", "onboarding", "offboarding", "benefits",
    "organizational structure", "organizational chart", "org chart",
    "departmental roles", "job title", "job titles",
    "employees", "staff", "team members",
    "performance review", "performance issues",
    "device issues", "peripheral device", "keyboard", "mouse", "monitor",
    "workstation", "equipment", "hardware", "software issues",
]


# ===== 2c. General Inquiry / service info keywords =====
general_keywords = [
    "service is delivered within", "within 24 to 48 hours",
    "support is accessible", "available via email", "available via phone", "available via chat",
    "brochures", "pricing information", "product information",
    "case studies", "documentation", "guides", "manuals",
    "general inquiry", "more information about",
    "difficulties with the process", "procedure", "process overview"
]


def is_noise_sentence(s: str) -> bool:
    for pattern in noise_patterns:
        if re.search(pattern, s, flags=re.IGNORECASE):
            return True
    return False


def contains_any_keyword(s_lower: str, keywords) -> bool:
    for kw in keywords:
        if re.search(r"\b" + re.escape(kw) + r"\b", s_lower):
            return True
    return False


def is_policy_sentence(s: str) -> bool:
    s_lower = s.lower()
    return (
        contains_any_keyword(s_lower, returns_keywords)
        or contains_any_keyword(s_lower, hr_keywords)
        or contains_any_keyword(s_lower, general_keywords)
    )


def clean_answer(answer: str) -> str:
    """Keep only non-noise sentences that contain returns / HR / general policy info."""
    if not isinstance(answer, str) or not answer.strip():
        return ""

    sentences = simple_sent_tokenize(answer)
    clean_sentences = []

    for s in sentences:
        s_strip = s.strip()
        if not s_strip:
            continue

        if is_noise_sentence(s_strip):
            continue

        if is_policy_sentence(s_strip):
            clean_sentences.append(s_strip)

    if not clean_sentences:
        return ""

    clean_sentences = list(dict.fromkeys(clean_sentences))
    return ". ".join(clean_sentences) + "."


def main():
    input_path = "/Users/shawn/Desktop/internship/UC-25-Summer-DATA601-AI-Agents/UC-25-Summer-DATA601-AI-Agents/RAG_policy/Human+General+Returns.csv"
    output_path = "/Users/shawn/Desktop/internship/UC-25-Summer-DATA601-AI-Agents/UC-25-Summer-DATA601-AI-Agents/RAG_policy/Human-General-Returns_cleaned.csv"

    print(f"Reading: {input_path}")
    df = pd.read_csv(input_path)

    candidate_cols = ["answer", "Answer", "response", "Response", "answer_text", "text"]
    answer_col = None
    for c in candidate_cols:
        if c in df.columns:
            answer_col = c
            break
    if answer_col is None:
        print(f"Available columns: {list(df.columns)}")
        raise ValueError("No answer column found.")

    print(f"Using column: {answer_col}")
    print("Cleaning answers...")
    df["cleaned_answer"] = df[answer_col].apply(clean_answer)

    df_clean = df[df["cleaned_answer"].str.strip() != ""].copy()
    keep_cols = ["cleaned_answer"]
    for c in ["question", "Question", "intent", "Intent", answer_col]:
        if c in df.columns:
            keep_cols.append(c)

    df_clean = df_clean[keep_cols]

    before = len(df)
    after = len(df_clean)
    print(f"Before: {before} rows, After: {after} rows ({after/before*100:.1f}% kept)")

    df_clean.to_csv(output_path, index=False)
    print(f"✅ Cleaned file saved: {output_path}")


if __name__ == "__main__":
    main()
