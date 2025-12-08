import re
import pandas as pd


# ===== 0. Simple sentence tokenizer (no NLTK) =====
def simple_sent_tokenize(text: str):
    """A very simple English sentence splitter."""
    if not isinstance(text, str):
        return []
    # Replace line breaks with spaces, then split by . ? !
    text = text.replace("\n", " ")
    parts = re.split(r"[.!?]+", text)
    # Remove empty segments
    return [p.strip() for p in parts if p.strip()]


# ===== 1. Define regex patterns for noisy sentences =====
noise_patterns = [
    # Opening thanks / apologies / appreciation
    r"^(thank you|thanks|we appreciate|we apologize|we are sorry)\b",
    # Asking the user to provide information
    r"(could you please|please provide|kindly provide|please send|please share)",
    # Phone / call arrangement
    r"(call|phone|convenient time)",
    # Angle‑bracket placeholders (<name> <acc_num> etc.)
    r"<\s*(name|tel_num|acc_num|email|order_num)\s*>",
    # Soothing / transition sentences
    r"(we understand|we are committed|feel free to reach)"
]

# ===== 2. Policy keywords =====
policy_keywords = [
    'billing period', 'billing cycle', 'due date', 'payment', 'payments due',
    'invoice', 'invoices', 'statement', 'statements',
    'late fee', 'late fees', 'fee', 'fees', '% per month',
    'credit card', 'bank transfer', 'paypal', 'online payment',
    'charges', 'billing discrepancies', 'billing errors', 'refund', 'credits'
]

def is_noise_sentence(s: str) -> bool:
    """Return True if the sentence matches any noise pattern."""
    for pattern in noise_patterns:
        if re.search(pattern, s, flags=re.IGNORECASE):
            return True
    return False

def is_policy_sentence(s: str) -> bool:
    """Return True if the sentence contains any policy keyword."""
    s_lower = s.lower()
    for kw in policy_keywords:
        if re.search(r"\b" + re.escape(kw) + r"\b", s_lower):
            return True
    return False

def clean_answer(answer: str) -> str:
    """Clean a single answer and return the concatenated policy sentences."""
    if not isinstance(answer, str) or not answer.strip():
        return ""

    # Sentence tokenization
    sentences = simple_sent_tokenize(answer)

    clean_sentences = []
    for s in sentences:
        s_strip = s.strip()
        if not s_strip:
            continue
        # 1) Skip noise
        if is_noise_sentence(s_strip):
            continue
        # 2) Keep only policy sentences
        if is_policy_sentence(s_strip):
            clean_sentences.append(s_strip)

    # Join kept sentences back, adding period at the end
    return ". ".join(clean_sentences) + ('.' if clean_sentences else '')

def main():
    # Read original CSV
    input_path = "/Users/shawn/Desktop/internship/UC-25-Summer-DATA601-AI-Agents/UC-25-Summer-DATA601-AI-Agents/RAG_policy/ Billing and Payments.csv"
    output_path = "/Users/shawn/Desktop/internship/UC-25-Summer-DATA601-AI-Agents/UC-25-Summer-DATA601-AI-Agents/RAG_policy/ Billing and Payments cleaned.csv"

    print(f"Reading: {input_path}")
    df = pd.read_csv(input_path)

    if "answer" not in df.columns:
        raise ValueError("Column 'answer' not found in CSV. Please check the column name.")

    print("Cleaning answers...")
    df["cleaned_answer"] = df["answer"].apply(clean_answer)
    # no empty cleaned_answer
    df = df[ df["cleaned_answer"].str.strip() != "" ]
    df = df[["cleaned_answer"]]

    df.to_csv(output_path, index=False)
    print(f"Done. Cleaned file saved to: {output_path}")

if __name__ == "__main__":
    main()
