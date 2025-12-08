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


# ===== 1. Pre-Sales noise patterns (customer service + scheduling) =====
noise_patterns = [
    # Opening/closing pleasantries
    r"^(thank you|thanks|we appreciate|we apologize|we are sorry|sorry for the inconvenience)\b",
    r"(have a great day|let us know if you have any other questions|we are here to help)",
    # Requests for information/call scheduling
    r"(could you please|please provide|kindly provide|please send|please share|provide details)",
    r"(call|phone|convenient time|schedule a call|contact telnum|let us know a suitable time)",
    # Placeholders
    r"<\s*(name|tel_num|acc_num|email|order_num|account number|customer id)\s*>",
    r"\btelnum\b|\baccnum\b|\bwebsiteurl\b",
    # General soothing phrases
    r"(we understand|we are committed|feel free to reach|happy to assist|glad to help)"
]


# ===== 2. Pre-Sales core keywords (features/pricing/demo) =====
policy_keywords = [
    # Product features/capabilities
    "features", "functionality", "capabilities", "integration", "integrations", "api", "apis",
    "customization", "customizable", "scalability", "scalable", "performance", "security",
    "encryption", "access control", "authentication", "dashboard", "analytics", "reporting",
    
    # Pricing/Plans
    "pricing", "plans", "cost", "quote", "subscription", "trial", "free trial", "demo",
    "enterprise", "premium", "basic", "pro", "licensing", "discount",
    
    # Demo/Evaluation
    "demo", "demonstration", "evaluation", "proof of concept", "pilot", "test",
    
    # Technical specs
    "system requirements", "specifications", "compatibility", "processor", "ram", "storage",
    "operating system", "browser", "version", "firmware",
    
    # Business value
    "optimize", "optimization", "efficiency", "productivity", "collaboration", "workflow",
    "brand growth", "digital strategy", "seo", "social media", "campaign",
    
    # Domain-specific (from samples)
    "data analytics", "investment optimization", "project management", "saas", "cloud"
]


def is_noise_sentence(s: str) -> bool:
    for pattern in noise_patterns:
        if re.search(pattern, s, flags=re.IGNORECASE):
            return True
    return False


def is_policy_sentence(s: str) -> bool:
    s_lower = s.lower()
    for kw in policy_keywords:
        if re.search(r"\b" + re.escape(kw) + r"\b", s_lower):
            return True
    return False


def clean_answer(answer: str) -> str:
    if not isinstance(answer, str) or not answer.strip():
        return ""

    sentences = simple_sent_tokenize(answer)
    clean_sentences = []

    for s in sentences:
        s_strip = s.strip()
        if not s_strip:
            continue
        # 1) Filter noise
        if is_noise_sentence(s_strip):
            continue
        # 2) Keep Pre-Sales technical sentences
        if is_policy_sentence(s_strip):
            clean_sentences.append(s_strip)

    if not clean_sentences:
        return ""

    # Deduplicate + join
    clean_sentences = list(dict.fromkeys(clean_sentences))
    return ". ".join(clean_sentences) + "."


def main():
    input_path = '/Users/shawn/Desktop/internship/UC-25-Summer-DATA601-AI-Agents/UC-25-Summer-DATA601-AI-Agents/RAG_policy/Customer & Pre-Sales Engagement.csv'
    output_path = '/Users/shawn/Desktop/internship/UC-25-Summer-DATA601-AI-Agents/UC-25-Summer-DATA601-AI-Agents/RAG_policy/Customer-Pre-Sales-Engagement_cleaned.csv'

    print(f"Reading: {input_path}")
    df = pd.read_csv(input_path)

    # Auto-detect answer column
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

    # Keep only non-empty results + key columns
    df_clean = df[df["cleaned_answer"].str.strip() != ""].copy()
    keep_cols = ["cleaned_answer"]
    for c in ["question", "Question", "intent", "Intent", answer_col]:
        if c in df.columns:
            keep_cols.append(c)
    
    df_clean = df_clean[keep_cols]
    
    # Output statistics
    before = len(df)
    after = len(df_clean)
    print(f"Before: {before} rows, After: {after} rows ({after/before*100:.1f}% kept)")

    df_clean.to_csv(output_path, index=False)
    print(f"Cleaned file saved: {output_path}")


if __name__ == "__main__":
    main()
