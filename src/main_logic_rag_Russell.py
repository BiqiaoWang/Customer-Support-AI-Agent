from typing import TypedDict
from langgraph.graph import StateGraph, END

import os
import re
import string
from datetime import datetime
from groq import Groq, APIStatusError
#  New  add
from qdrant_client import QdrantClient
from langchain_openai import AzureOpenAIEmbeddings



class State(TypedDict):
    # Original customer ticket text
    query: str

    # Stage 1: automatic understanding
    ticket_type: str          # e.g. "Technical", "Billing", "General"
    sentiment: str            # "Negative" or "Non-Negative"

    # Stage 1: automatic reply (to be filled by RAG agent)
    initial_reply: str        # reply generated from enterprise knowledge base / RAG

    # Workflow metadata
    escalation_reason: list[str]  # reasons collected for escalation decisions
    final_action: str             # AUTO_REPLY / ESCALATE / CLOSE
    status: str                   # NEW -> REPLIED -> (CLOSED or ESCALATED)
    events: list[str]             # simple log of steps taken
    turn: int                     # conversation turn counter
    history: list[dict]           # simple chat history [{"role": "...", "content": "..."}]
    created_at: str             # timestamp of first valid user message
    input_valid: bool             # validation result
    input_meaningful: bool        # noise detection result
    input_continue: bool          # follow-up routing flag
    restart_to_validate: bool     # restart flag for new ticket
    # removed apology flag
    risk_level: str               # for Billing and Payments: High / Low
    pending_question: str         # "", "resolution", or "escalation"
    resolution_no_count: int      # count of times user said "No" to resolution question

    # Stage 2: follow-up from the customer / UI
    user_feedback: str        # free-text feedback, e.g. "No, it is not fixed"
    resolved: bool            # did the customer confirm the issue is resolved?
    wants_human: bool         # did the customer clearly request a human agent?

    # Final decision & output
    escalated: bool           # whether this ticket should be escalated to a human
    response: str             # final reply to customer OR handover note

    #  New  add
    rag_context: str               # retrieved KB context text
    ragcards: list[str]           # optional: store policy card ids for citations/debug



MODEL = "llama-3.1-8b-instant"


# ==== RAG runtime (Qdrant + Azure OpenAI Embeddings) ==== # New add
QDRANT_URL = os.getenv("QDRANT_URL")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")
QDRANT_COLLECTION = os.getenv("QDRANT_COLLECTION", "supportkbcollection")

AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")
AZURE_OPENAI_API_KEY = os.getenv("AZURE_OPENAI_API_KEY")
AZURE_OPENAI_API_VERSION = os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-01")
AZURE_OPENAI_EMBED_DEPLOYMENT = os.getenv("AZURE_OPENAI_EMBED_DEPLOYMENT", "text-embedding-3-small")

qdrantclient = QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY)
ragembeddings = AzureOpenAIEmbeddings(
    model=AZURE_OPENAI_EMBED_DEPLOYMENT,
    azure_endpoint=AZURE_OPENAI_ENDPOINT,
    api_key=AZURE_OPENAI_API_KEY,
    openai_api_version=AZURE_OPENAI_API_VERSION,
)


client = Groq(api_key=os.getenv("GROQ_API_KEY"))

FALLBACK_USER_REPLY = (
    "We've recorded your issue. Please share your phone or email, and a teammate "
    "will reach out shortly."
)
GREETING = (
    "Hi, I'm an AI support assistant. I'll do my best to help you with your request. "
    "How may I help you today?"
)
ESCALATION_REPLY = (
    "We have clearly understood and recorded your question and request. "
    "We will resolve your issue as quickly as possible. Our helpful and professional staff "
    "will contact you shortly. Thank you for your patience!"
)
# CLOSING_PROMPT removed from responses per latest requirements


def llm_chat(system_prompt: str, user_prompt: str, max_tokens: int = 256) -> str:
    """Simple helper around the Groq client."""

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]

    try:
        completion = client.chat.completions.create(
            model=MODEL,
            messages=messages,
            max_tokens=max_tokens,
        )
    except APIStatusError as exc:
        raise RuntimeError(f"Groq API error: {exc}") from exc

    choice = completion.choices[0]
    # Groq returns OpenAI-style responses; guard against missing content.
    return (choice.message.content or "").strip()


def _append_event(state: State, message: str) -> list[str]:
    """Append a short event string to the state log."""
    events = list(state.get("events") or [])
    events.append(message)
    return events


def _append_reason(state: State, reason: str) -> list[str]:
    """Append an escalation reason."""
    reasons = list(state.get("escalation_reason") or [])
    reasons.append(reason)
    return reasons


def _format_history(history: list[dict], max_items: int = 10) -> str:
    """Render recent history lines for prompts."""
    if not history:
        return ""
    recent = history[-max_items:]
    return "\n".join(f"{item.get('role', 'unknown')}: {item.get('content', '')}" for item in recent)


def _has_heading(text: str) -> bool:
    """Detect if the text starts with a heading/label we do not want."""
    stripped = text.strip()
    if not stripped:
        return False
    first_line = stripped.splitlines()[0].strip()
    if first_line.startswith("#"):
        return True
    if ":" in first_line and len(first_line.split(":")[0]) <= 60:
        return True
    keywords = ["handover", "note", "for human", "agent"]
    lowered = first_line.lower()
    return any(k in lowered for k in keywords)


def _clean_llm_reply(text: str) -> str:
    cleaned = (text or "").strip()
    if not cleaned:
        return ""

    cleaned = re.sub(r"^(answer|response|reply)\s*:\s*", "", cleaned, flags=re.IGNORECASE)
    sentences = re.split(r"(?<=[.!?])\s+", cleaned)
    filtered = []
    for sentence in sentences:
        s = sentence.strip()
        if not s:
            continue
        if "?" in s:
            continue
        lower = s.lower()
        if any(
            phrase in lower
            for phrase in (
                "let me know",
                "feel free",
                "if you need",
                "if you have any",
                "hope this helps",
                "happy to help",
                "glad to help",
                "reach out",
            )
        ):
            continue
        filtered.append(s)
    cleaned = " ".join(filtered).strip()
    if not cleaned:
        return ""

    fillers = (
        "sure,",
        "sure.",
        "sure!",
        "certainly,",
        "certainly.",
        "of course,",
        "of course.",
        "absolutely,",
        "absolutely.",
        "no problem,",
        "no problem.",
        "hi,",
        "hello,",
        "thanks,",
        "thanks.",
        "thank you,",
        "thank you.",
    )
    lowered = cleaned.lower()
    for prefix in fillers:
        if lowered.startswith(prefix):
            cleaned = cleaned[len(prefix):].lstrip()
            break
    return cleaned


def _classify_sentiment(system_prompt: str, user_prompt: str, max_attempts: int = 5, event_label: str = "sentiment") -> tuple[str, list[str], bool]:
    """Return Negative/Non-Negative with retries when output is invalid."""
    allowed = {"negative": "Negative", "non-negative": "Non-Negative"}
    events: list[str] = []
    had_error = False
    for attempt in range(1, max_attempts + 1):
        raw = ""
        try:
            raw = llm_chat(system_prompt, user_prompt, max_tokens=4).strip()
        except Exception as exc:
            had_error = True
            events.append(f"{event_label} -> llm error (attempt {attempt}: {exc})")
            continue
        normalized = raw.lower()
        if normalized in allowed:
            events.append(f"{event_label} -> {allowed[normalized]} (attempt {attempt})")
            return allowed[normalized], events, had_error
        events.append(f"{event_label} -> retry (invalid: {raw}, attempt {attempt})")
    events.append(f"{event_label} -> fallback Non-Negative")
    return "Non-Negative", events, had_error


def _ensure_created_at(state: State) -> str:
    """Return created_at timestamp for the first valid user message."""
    created_at = state.get("created_at")
    if created_at:
        return created_at
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def validate_input(state: State) -> dict:
    """Validate user input length and characters (<=200, ASCII letters/numbers/punctuation/spaces)."""
    query = state.get("query") or ""
    length = len(query)

    def _is_allowed_char(ch: str) -> bool:
        return ch.isascii() and (ch.isalnum() or ch.isspace() or ch in string.punctuation)

    invalid_chars = [ch for ch in query if not _is_allowed_char(ch)]

    events = _append_event(state, "validate_input -> start")
    if length == 0 or length > 200 or invalid_chars:
        reasons = []
        if length == 0:
            reasons.append("empty input")
        if length > 200:
            reasons.append(f"length {length} > 200")
        if invalid_chars:
            reasons.append("invalid characters")

        if length == 0:
            message = "Your input is empty. Please enter your request (max 200 characters)."
        else:
            message = (
                "Please keep your request within 200 characters using English letters, "
                "numbers, punctuation, and spaces only."
            )
            if length > 200:
                message += f" Current length: {length}."

        events = _append_event(
            {"events": events},
            f"validate_input -> reject ({'; '.join(reasons)})",
        )
        history = list(state.get("history") or [])
        history.append({"role": "user", "content": query})
        return {
            "input_valid": False,
            "response": message,
            "status": "REPLIED",
            "final_action": "AUTO_REPLY",
            "escalated": False,
            "events": events,
            "history": history,
        }

    events = _append_event({"events": events}, "validate_input -> ok")
    created_at = state.get("created_at") or _ensure_created_at(state)
    return {"input_valid": True, "events": events, "created_at": created_at}


def detect_noise(state: State) -> dict:
    """Noise filter removed; always pass through."""
    return {"input_meaningful": True}


def detect_human_request(state: State) -> dict:
    """Detect explicit requests for a human agent; escalate immediately if found."""
    history_text = _format_history(state.get("history") or [])
    history_block = f"Conversation so far (last turns):\n{history_text}\n\n" if history_text else ""

    system_prompt = (
        "You are a detector for explicit human support requests. "
        "If the user clearly asks to talk to a human/agent/support person, answer exactly: yes. "
        "Otherwise answer: no."
    )
    user_prompt = (
        f"{history_block}"
        f"Current user message:\n{state.get('query')}"
    )

    wants_human = False
    events = _append_event(state, "detect_human_request -> start")
    try:
        human_verdict = llm_chat(system_prompt, user_prompt, max_tokens=3).strip().lower()
        wants_human = human_verdict == "yes"
    except Exception as exc:
        events = _append_event({"events": events}, f"detect_human_request -> skipped (llm error: {exc})")

    if not wants_human:
        lowered = (state.get("query") or "").lower()
        keywords = [
            "human",
            "agent",
            "real person",
            "customer service",
            "manual support",
            "talk to someone",
            "speak to someone",
            "live representative",
        ]
        wants_human = any(k in lowered for k in keywords)

    if wants_human:
        history = list(state.get("history") or [])
        history.append({"role": "user", "content": state.get("query", "")})
        reasons = _append_reason(state, "user_requested_human")
        events = _append_event({"events": events}, "detect_human_request -> escalate")
        return {
            "escalated": True,
            "final_action": "ESCALATE",
            "status": "ESCALATED",
            "events": events,
            "history": history,
            "escalation_reason": reasons,
            "pending_question": "",
        }

    events = _append_event({"events": events}, "detect_human_request -> no")
    return {"escalated": False, "events": events}


def detect_negative_turn(state: State) -> dict:
    """From the second turn onward, detect Negative sentiment and escalate immediately."""
    events = _append_event(state, "detect_negative -> start")
    pending = state.get("pending_question") or ""
    if pending:
        events = _append_event({"events": events}, f"detect_negative -> skip (pending {pending})")
        return {"escalated": False, "events": events}

    query = (state.get("query") or "").strip()
    lowered = query.lower()
    no_patterns = [
        "no",
        "nope",
        "nah",
        "not yet",
        "not really",
        "still not",
        "still broken",
        "not fixed",
        "no it is not",
        "it is not fixed",
    ]

    def _matches(patterns: list[str]) -> bool:
        return any(lowered == p or lowered.startswith(p + " ") for p in patterns)

    if _matches(no_patterns):
        events = _append_event({"events": events}, "detect_negative -> skip (user said no)")
        return {"escalated": False, "events": events}

    turn = int(state.get("turn") or 1)
    if turn < 2:
        events = _append_event({"events": events}, "detect_negative -> skip (turn<2)")
        return {"escalated": False, "events": events}

    history_text = _format_history(state.get("history") or [])
    history_block = f"Conversation so far (last turns):\n{history_text}\n\n" if history_text else ""
    system_prompt = (
        "You are a sentiment classifier. "
        "If the user's message is Negative, answer exactly: Negative. "
        "Otherwise answer: Non-Negative."
    )
    user_prompt = (
        f"{history_block}"
        f"Current user message:\n{state.get('query')}"
    )

    sentiment, attempt_events, _ = _classify_sentiment(
        system_prompt,
        user_prompt,
        max_attempts=10,
        event_label="detect_negative",
    )
    for entry in attempt_events:
        events = _append_event({"events": events}, entry)

    if sentiment == "Negative":
        history = list(state.get("history") or [])
        history.append({"role": "user", "content": state.get("query", "")})
        reasons = _append_reason(state, "negative_sentiment")
        events = _append_event({"events": events}, "detect_negative -> escalate")
        return {
            "escalated": True,
            "final_action": "ESCALATE",
            "status": "ESCALATED",
            "events": events,
            "history": history,
            "escalation_reason": reasons,
            "sentiment": "Negative",
            "pending_question": "",
        }

    events = _append_event({"events": events}, "detect_negative -> non-negative")
    return {"escalated": False, "events": events}


def route_after_decision(state: State) -> str:
    """Router: after the decision node, choose the next step."""
    return "escalate" if state.get("escalated") else "handle_response"


def route_after_validation(state: State) -> str:
    """Router: after validation, either proceed or stop."""
    if not state.get("input_valid"):
        return "end"
    return "detect_human_request"


def route_after_human_request(state: State) -> str:
    """Router: after explicit human request detection."""
    if state.get("escalated"):
        return "escalate"
    if state.get("pending_question"):
        return "check_followup"
    return "detect_negative"


def route_after_negative(state: State) -> str:
    """Router: after negative detection, route to follow-up or continue."""
    if state.get("escalated"):
        return "escalate"
    if state.get("pending_question"):
        return "check_followup"
    return "categorize"


def route_after_noise_check(state: State) -> str:
    """Router: after noise detection, proceed or stop."""
    if not state.get("input_meaningful", True):
        return "end"
    return "categorize"


def check_followup(state: State) -> dict:
    """Handle follow-ups, yes/no answers, abusive messages, and restart for new tickets."""

    query = (state.get("query") or "").strip()
    events = _append_event(state, "check_followup -> start")
    history = list(state.get("history") or [])
    pending = state.get("pending_question") or ""
    resolution_no_count = int(state.get("resolution_no_count") or 0)
    restart_to_validate = False
    turn = int(state.get("turn") or 1)

    lowered = query.lower()
    yes_patterns = ["yes", "y", "yeah", "yep", "sure", "ok", "okay", "affirmative", "resolved"]
    no_patterns = [
        "no",
        "nope",
        "nah",
        "not yet",
        "not really",
        "still not",
        "still broken",
        "not fixed",
        "no it is not",
        "it is not fixed",
    ]

    def _matches(patterns: list[str]) -> bool:
        return any(lowered == p or lowered.startswith(p + " ") for p in patterns)

    # Pending resolution confirmation
    if pending == "resolution":
        if _matches(yes_patterns):
            response = "Great to hear it's resolved. We'll close this ticket."
            history.append({"role": "user", "content": query})
            history.append({"role": "assistant", "content": response})
            events = _append_event({"events": events}, "check_followup -> resolved confirmed")
            return {
                "input_continue": False,
                "response": response,
                "status": "CLOSED",
                "final_action": "CLOSE",
                "escalated": False,
                "events": events,
                "history": history,
                "pending_question": "",
                "resolution_no_count": 0,
            }
        if _matches(no_patterns):
            history.append({"role": "user", "content": query})
            resolution_no_count += 1
            # From second round onward, and after accumulating at least 2 "No" answers to this resolution question, ask about escalation.
            if turn >= 2 and resolution_no_count >= 2:
                response = "Would you like us to escalate your issue to a human agent? Please reply Yes or No."
                events = _append_event({"events": events}, "check_followup -> ask escalate (turn>=2 after no)")
                history.append({"role": "assistant", "content": response})
                return {
                    "input_continue": False,
                    "response": response,
                    "status": "REPLIED",
                    "final_action": "AUTO_REPLY",
                    "escalated": False,
                    "events": events,
                    "history": history,
                    "pending_question": "escalation",
                    "resolution_no_count": resolution_no_count,
                }
            response = "Could you describe your issue in more detail so we can better assist you?"
            events = _append_event({"events": events}, "check_followup -> prompt for details (user said no)")
            history.append({"role": "assistant", "content": response})
            return {
                "input_continue": False,
                "response": response,
                "status": "REPLIED",
                "final_action": "AUTO_REPLY",
                "escalated": False,
                "events": events,
                "history": history,
                "pending_question": "",
                "resolution_no_count": resolution_no_count,
            }

    # Pending escalation decision
    if pending == "escalation":
        if _matches(yes_patterns):
            response = ESCALATION_REPLY
            history.append({"role": "user", "content": query})
            history.append({"role": "assistant", "content": response})
            events = _append_event({"events": events}, "check_followup -> user requested escalation")
            reasons = _append_reason(state, "negative_feedback")
            return {
                "input_continue": False,
                "response": response,
                "status": "ESCALATED",
                "final_action": "ESCALATE",
                "escalated": True,
                "events": events,
                "history": history,
                "sentiment": "Negative",
                "escalation_reason": reasons,
                "pending_question": "",
                "resolution_no_count": resolution_no_count,
            }
        if _matches(no_patterns):
            response = "Could you describe your issue in more detail so we can better assist you?"
            events = _append_event({"events": events}, "check_followup -> user declined escalation")
            history.append({"role": "user", "content": query})
            history.append({"role": "assistant", "content": response})
            return {
                "input_continue": False,
                "response": response,
                "status": state.get("status") or "REPLIED",
                "final_action": state.get("final_action") or "AUTO_REPLY",
                "escalated": False,
                "events": events,
                "history": history,
                "pending_question": "",
                "resolution_no_count": resolution_no_count,
            }

    events = _append_event({"events": events}, "check_followup -> continue")
    return {
        "input_continue": True,
        "events": events,
        "pending_question": pending,
        "resolution_no_count": resolution_no_count,
        "restart_to_validate": restart_to_validate,
    }


def route_after_followup(state: State) -> str:
    """Router: after followup checks, proceed or stop."""
    if not state.get("input_continue", True):
        return "end"
    if state.get("restart_to_validate"):
        return "validate_input"
    return "categorize"


def route_after_categorize(state: State) -> str:
    """Router: after categorize, decide next step (no sentiment in first round)."""
    if (state.get("ticket_type") or "").lower() == "billing and payments":
        return "assess_billing_risk"
    # New change
    return "retrieve_rag_context"


def route_after_billing_risk(state: State) -> str:
    """Router: after billing risk, escalate if high, else continue."""
    return "escalate" if state.get("escalated") else "retrieve_rag_context"


def greet(state: State) -> dict:
    """Initial greeting before any user input is processed."""
    history = list(state.get("history") or [])
    turn = int(state.get("turn") or 0)
    status = state.get("status") or "NEW"

    # If this is an ongoing ticket (history/turn present), skip greeting.
    if history or turn > 0:
        events = _append_event(state, "greet -> skip (ongoing conversation)")
        return {"history": history, "events": events, "status": status}

    history.append({"role": "assistant", "content": GREETING})
    events = _append_event(state, "greet -> initial assistant message")
    response = state.get("response") or GREETING
    return {
        "history": history,
        "events": events,
        "status": status,
        "response": response,
    }


# 1. Classifier Agent
def categorize(state: State) -> dict:
    """Classify the ticket into a high-level ticket_type.

    This is the first step of the workflow and writes only `ticket_type`
    into the shared state.
    """
    # Ensure base metadata
    status = state.get("status") or "NEW"
    escalation_reason = list(state.get("escalation_reason") or [])
    turn = int(state.get("turn") or 0) + 1
    history = list(state.get("history") or [])
    history.append({"role": "user", "content": state["query"]})
    events = _append_event(state, f"turn {turn} start -> {status}")

    system_prompt = (
        "You are a customer support ticket classifier. Choose exactly ONE category "
        "from the list below based on the user's request. Return only the category "
        "name, no explanation.\n\n"
        "Categories and definitions:\n"
        "1. Account: All requests involving the identity and access of a user account, "
        "including login/password reset, multi-factor authentication, account "
        "configuration errors, insufficient permissions, access requests to systems or "
        "platforms (such as email, cloud storage, CRM, code repositories, etc.), "
        "authorization changes, or situations where access to the account is "
        "unavailable, should be categorized as \"account\".\n"
        "2. Billing and Payments: All requests concerning fees, bills, or payments "
        "themselves -- including billing cycles, invoice details, billing structures, "
        "prices and packages, payment methods, payment failures or delays, fee "
        "discrepancies, billing errors, refunds, or dispute resolution -- that are "
        'directly related to "how money is calculated, invoiced, and paid" should be '
        "categorized as Billing and Payments.\n"
        "3. IT & Technical Support: All questions that focus on \"how to configure, "
        "integrate, upgrade, troubleshoot, or restore normal operation of a system, "
        "software, hardware, or network,\" including technical setup guidance, system "
        "integration, infrastructure upgrades, performance or stability failures, "
        "configuration requests, hardware/software/network anomalies and "
        "troubleshooting, and which do not involve account permissions or billing, "
        "should be categorized as IT & Technical Support.\n"
        "4. Returns & Exchange: All requests concerning the return or exchange of "
        "purchased goods, including return/exchange policies and eligibility, return "
        "time limits and conditions, process steps, system errors, status inquiries, "
        "refund or exchange progress, etc., and provided that \"the goods have been "
        "purchased and need to be returned or exchanged\", should be classified as "
        "Returns & Exchange.\n"
        "5. Sales & Pre-sales: All inquiries whose core purpose is to \"assess the "
        "suitability of a product/service before purchase or formal use,\" including "
        "requests regarding product features and specifications, technical "
        "architecture, security and compliance, pricing and packages, discounts and "
        "promotions, integration capabilities, application scenarios or business value "
        "descriptions, and which have not yet entered the specific fault or account "
        "execution stage, should be classified as Sales & Pre-sales.\n"
        "6. Security: Any issue that focuses on \"protecting systems, accounts, or data "
        "from security threats,\" including authentication and multi-factor "
        "authentication (MFA), security policy and group policy enforcement, security "
        "configuration and compliance, phishing/suspicious email reporting, and "
        "investigation of potential vulnerabilities or security risks, and whose "
        "emphasis is on security protection rather than ordinary access or function "
        "usage requests, should be classified as Security.\n"
        "7. General: All questions that do not clearly fall under the six categories of "
        "Account, Billing & Payments, IT & Technical Support, Sales & Pre-sales, "
        "Returns & Exchange, or Security, information requests that are not specific "
        "or that are difficult to categorize should be classified as General."
    )
    allowed_exact = [
        "Account",
        "Billing and Payments",
        "IT & Technical Support",
        "Returns & Exchange",
        "Sales & Pre-sales",
        "Security",
        "General",
    ]
    history_text = _format_history(history)
    history_block = f"Conversation so far (last turns):\n{history_text}\n\n" if history_text else ""
    base_user_prompt = (
        f"{history_block}"
        f"Current turn: {turn}\n"
        f"Customer query:\n{state['query']}\n\n"
        "Answer with exactly one category name from this list:\n"
        "Account\n"
        "Billing and Payments\n"
        "IT & Technical Support\n"
        "Returns & Exchange\n"
        "Sales & Pre-sales\n"
        "Security\n"
        "General"
    )

    ticket_type = "General"
    try:
        max_attempts = 10
        for attempt in range(1, max_attempts + 1):
            prompt = base_user_prompt
            if attempt > 1:
                prompt += "\nYour previous answer was not an exact match. Respond with exactly one of the seven category names above."

            ticket_type_raw = llm_chat(system_prompt, prompt).strip()
            if ticket_type_raw in allowed_exact:
                ticket_type = ticket_type_raw
                events = _append_event({"events": events}, f"categorize -> {ticket_type} (attempt {attempt})")
                break
            if attempt == max_attempts:
                escalation_reason.append("low_confidence_ticket_type")
                events = _append_event(
                    {"events": events},
                    f"categorize -> fallback General (invalid: {ticket_type_raw}, attempt {attempt})",
                )
            else:
                events = _append_event(
                    {"events": events},
                    f"categorize -> retry (invalid: {ticket_type_raw}, attempt {attempt})",
                )
        else:
            escalation_reason.append("low_confidence_ticket_type")
    except Exception as exc:
        ticket_type = "General"
        escalation_reason.append("llm_failure")
        events = _append_event(
            {"events": events}, f"categorize -> fallback (llm error: {exc})"
        )

    return {
        "ticket_type": ticket_type,
        "escalation_reason": escalation_reason,
        "status": status,
        "events": events,
        "turn": turn,
        "history": history,
        "risk_level": state.get("risk_level") or "",
        "sentiment": state.get("sentiment") or "Non-Negative",
    }


# Billing Risk Assessment
def assess_billing_risk(state: State) -> dict:
    """Assess Billing and Payments tickets; default High unless clearly read-only."""
    text = (state.get("query") or "").lower()
    events = _append_event(state, "assess_billing_risk -> start")

    # High-risk triggers any potential money change.
    high_keywords = [
        "refund",
        "chargeback",
        "charged twice",
        "double charge",
        "wrong amount",
        "incorrect amount",
        "overcharged",
        "undercharged",
        "billing error",
        "dispute",
        "unauthorized",
        "unauthorized deduction",
        "credit",
        "compensation",
        "adjustment",
        "charge wrong",
        "deducting",
        "deduction",
        "deduct",
        "deducted",
        "without my consent",
        "without consent",
        "without permission",
        "without my permission",
        "give me my money back",
        "money back",
        "unauthorized charge",
    ]

    low_keywords = [
        "view bill",
        "see bill",
        "view my bill",
        "billing cycle",
        "billing period",
        "invoice",
        "download invoice",
        "fee breakdown",
        "explain charges",
        "explanation of charges",
        "why was i charged",
        "billing rules",
        "payment method",
        "payment methods",
        "payment option",
        "payment options",
        "payment types",
        "how to pay",
        "pay with",
        "accepted payment",
        "accepted payments",
    ]

    risk_level = "High"
    for kw in high_keywords:
        if kw in text:
            events = _append_event({"events": events}, f"assess_billing_risk -> High (keyword: {kw})")
            risk_level = "High"
            break
    else:
        for kw in low_keywords:
            if kw in text:
                events = _append_event({"events": events}, f"assess_billing_risk -> Low (keyword: {kw})")
                risk_level = "Low"
                break

    # If High, short-circuit to escalation.
    if risk_level == "High":
        reasons = _append_reason(state, "billing_high_risk")
        return {
            "risk_level": risk_level,
            "events": events,
            "escalated": True,
            "final_action": "ESCALATE",
            "status": "ESCALATED",
            "pending_question": "",
            "escalation_reason": reasons,
        }

    return {"risk_level": risk_level, "events": events, "sentiment": state.get("sentiment") or "Non-Negative"}


# 2. Sentiment Agent
def analyze_sentiment(state: State) -> dict:
    """Sentiment analysis for the current ticket."""
    history_text = _format_history(state.get("history") or [])
    history_block = f"Conversation so far (last turns):\n{history_text}\n\n" if history_text else ""

    system_prompt = (
        "You are a sentiment analysis assistant for customer support. "
        "Classify sentiment as Negative or Non-Negative."
    )
    user_prompt = (
        f"{history_block}"
        f"Current turn: {state.get('turn') or 1}\n"
        f"Customer query:\n{state['query']}\n\n"
        "Only answer with one word: Negative or Non-Negative."
    )

    sentiment, attempt_events, had_error = _classify_sentiment(
        system_prompt,
        user_prompt,
        max_attempts=10,
        event_label="sentiment",
    )
    events = list(state.get("events") or [])
    for entry in attempt_events:
        events = _append_event({"events": events}, entry)
    if had_error:
        reasons = _append_reason(state, "llm_failure")
        return {"sentiment": sentiment, "events": events, "escalation_reason": reasons}
    return {"sentiment": sentiment, "events": events}


# 3. Initial Reply Agent (RAG placeholder) 

def retrieve_rag_context(state: State) -> dict:
    query = (state.get("query") or "").strip()
    events = list(state.get("events") or [])
    events.append("retrieve_rag_context - start")

    if not query:
        events.append("retrieve_rag_context - empty query")
        return {"rag_context": "", "ragcards": [], "events": events}

    try:
        vec = ragembeddings.embed_query(query)
        res = qdrantclient.query_points(
            collection_name=QDRANT_COLLECTION,
            query=vec,
            limit=5,
            with_payload=True,
        )
        hits = res.points if hasattr(res, "points") else res
    except Exception as exc:
        events.append(f"retrieve_rag_context - error {exc}")
        return {"rag_context": "", "ragcards": [], "events": events}

    cards = []
    chunks = []
    for h in hits:
        payload = getattr(h, "payload", None) or {}
        text = (payload.get("text") or "").strip()
        p = (payload.get("p") or "").strip()
        v = (payload.get("v") or "").strip()
        c = (payload.get("c") or "").strip()

        if c:
            cards.append(c)
        if text:
            header = f"[{c}] {p} {v}".strip()
            chunks.append(f"{header}\n{text}".strip())

    rag_context = "\n---\n".join(chunks).strip()
    events.append(f"retrieve_rag_context - len {len(chunks)} chunks")
    return {"rag_context": rag_context, "ragcards": cards, "events": events}




def generate_first_round_reply(state: State) -> dict:
    """Generate the first automatic reply.

    IMPORTANT: RAG retrieval is not implemented yet. This slot handles the first
    model reply for specific ticket types, and keeps a placeholder when we skip.
    """

    ticket_type = (state.get("ticket_type") or "").lower()
    auto_types = {
        "account",
        "it & technical support",
        "returns & exchange",
        "general",
        "billing and payments",  # low-risk only; high-risk will be escalated
    }

    history_text = _format_history(state.get("history") or [])
    history_block = f"Conversation so far (last turns):\n{history_text}\n\n" if history_text else ""
    rag_context = state.get("rag_context") or ""
    context_block = f"RAG context (use this first):\n{rag_context}\n\n" if rag_context else ""
    user_prompt = (
        f"{history_block}"
        f"{context_block}"
        f"Ticket type: {state.get('ticket_type')}\n"
        f"Customer query:\n{state.get('query', '')}\n\n"
        "Answer the user's question directly in 1-2 concise sentences. "
        "Do not ask follow-up questions. Do not add greetings, apologies, or offers. "
        "Keep under 120 words."
    )
    system_prompt = (
        "You are a customer support assistant. If RAG context is provided, use it as the primary source. "
        "If no relevant context is present, answer from your own knowledge but stay accurate, specific, and respectful. "
        "Do not ask questions or add conversational filler. "
        "Do not promise refunds, policy exceptions, or irreversible actions. "
        "Keep the tone concise and direct."
    )

    initial_reply = state.get("initial_reply") or ""
    events = _append_event(state, "initial_reply -> placeholder")

    # Billing only allowed for auto-reply if risk is Low
    if ticket_type == "billing and payments" and (state.get("risk_level") or "").lower() != "low":
        events = _append_event(
            {"events": events},
            f"initial_reply -> skipped (billing high risk or unknown)",
        )
        return {"initial_reply": initial_reply, "events": events}

    if ticket_type not in auto_types:
        events = _append_event(
            {"events": events},
            f"initial_reply -> skipped (ticket_type {ticket_type or 'unknown'})",
        )
        return {"initial_reply": initial_reply, "events": events}

    try:
        initial_reply = llm_chat(system_prompt, user_prompt, max_tokens=256)
        cleaned_reply = _clean_llm_reply(initial_reply)
        if cleaned_reply:
            initial_reply = cleaned_reply
        else:
            initial_reply = FALLBACK_USER_REPLY
            events = _append_event(
                {"events": events},
                "initial_reply -> cleaned empty (fallback)",
            )
        events = _append_event(
            {"events": events},
            f"initial_reply -> generated ({state.get('ticket_type')})",
        )
    except Exception as exc:
        initial_reply = state.get("initial_reply") or FALLBACK_USER_REPLY
        events = _append_event(
            {"events": events},
            f"initial_reply -> fallback (llm error: {exc})",
        )
        escalation_reason = _append_reason(state, "llm_failure")
        return {
            "initial_reply": initial_reply,
            "events": events,
            "escalation_reason": escalation_reason,
        }

    return {"initial_reply": initial_reply, "events": events}


# 4. Escalation Decision Agent
def decide_escalation(state: State) -> dict:
    """Decide whether this ticket should be escalated to a human agent.

    The decision is based on:
      - ticket_type (e.g. transaction / billing related)
      - sentiment polarity
      - explicit user request for a human
      - whether the user has already confirmed the issue is resolved
    """
    ticket_type = (state.get("ticket_type") or "").lower()
    sentiment = (state.get("sentiment") or "").lower()
    risk_level = (state.get("risk_level") or "").lower()

    resolved = bool(state.get("resolved", False))
    wants_human = bool(state.get("wants_human", False))
    reasons = list(state.get("escalation_reason") or [])
    events = list(state.get("events") or [])
    llm_failure = "llm_failure" in reasons
    pending_question = state.get("pending_question") or ""
    auto_types = {
        "account",
        "it & technical support",
        "returns & exchange",
        "general",
    }

    # --- Example rule set, matching the narrative logic ---

    # If the customer already confirmed it's resolved, do NOT escalate.
    if resolved:
        events.append("decision -> close (already resolved)")
        return {
            "escalated": False,
            "final_action": "CLOSE",
            "status": "CLOSED",
            "events": events,
        }

    # 1) Certain ticket types are more sensitive.
    if ticket_type == "billing and payments":
        # Only escalate Billing when risk is High or unknown.
        if risk_level in ("high", ""):
            reasons = _append_reason({"escalation_reason": reasons}, "billing_sensitive")
            reasons = _append_reason({"escalation_reason": reasons}, "billing_high_risk")
    if ticket_type == "sales & pre-sales":
        reasons = _append_reason({"escalation_reason": reasons}, "sales_presales_sensitive")
    if ticket_type == "security":
        reasons = _append_reason({"escalation_reason": reasons}, "security_sensitive")

    # 2) Always respect a clear request for human support.
    if wants_human:
        reasons = _append_reason({"escalation_reason": reasons}, "user_requested_human")

    # 3) Escalate if the customer sentiment is negative.
    if sentiment == "negative":
        reasons = _append_reason({"escalation_reason": reasons}, "negative_sentiment")

    # 4) Low confidence classification (added earlier).
    if "low_confidence_ticket_type" in reasons:
        reasons = _append_reason({"escalation_reason": reasons}, "routing_uncertain")

    core_reasons = [r for r in reasons if r != "llm_failure"]

    if core_reasons:
        events.append(f"decision -> escalate (reasons: {', '.join(core_reasons)})")
        return {
            "escalated": True,
            "escalation_reason": reasons,
            "final_action": "ESCALATE",
            "status": "ESCALATED",
            "events": events,
            "pending_question": pending_question,
            "risk_level": risk_level,
        }

    if llm_failure:
        events.append("decision -> auto reply (llm fallback)")
        return {
            "escalated": False,
            "escalation_reason": reasons,
            "final_action": "AUTO_REPLY",
            "status": "REPLIED",
            "events": events,
        }

    events.append("decision -> stay automated")
    # Otherwise, keep it in the automated flow.
    return {
        "escalated": False,
        "escalation_reason": reasons,
        "status": state.get("status") or "NEW",
        "events": events,
        "pending_question": pending_question,
        "risk_level": risk_level,
    }


# 5. Final Response Agent (for non-escalated tickets)
def handle_response(state: State) -> dict:
    """Prepare the final reply to the customer when we do NOT escalate.

    In this workflow design, the actual content of the first reply should
    come from the RAG agent (enterprise knowledge base). Here we simply
    reuse `initial_reply` as the final response, and optionally add a
    gentle follow-up sentence.
    """
    llm_failure = "llm_failure" in (state.get("escalation_reason") or [])
    base_reply = state.get("initial_reply") or FALLBACK_USER_REPLY
    if llm_failure:
        base_reply = FALLBACK_USER_REPLY

    # If we know it is not resolved, encourage the user to ask for a human.
    resolved = bool(state.get("resolved", False))

    status = state.get("status") or "REPLIED"
    if status not in {"CLOSED", "ESCALATED"}:
        status = "REPLIED"
    final_action = state.get("final_action") or "AUTO_REPLY"

    # Add follow-up question for auto-reply tickets: always resolution check first.
    turn = int(state.get("turn") or 1)
    ticket_type = (state.get("ticket_type") or "").lower()
    risk_level = (state.get("risk_level") or "").lower()
    auto_types = {
        "account",
        "it & technical support",
        "returns & exchange",
        "general",
    }
    auto_reply_path = ticket_type in auto_types or (ticket_type == "billing and payments" and risk_level == "low")
    if auto_reply_path:
        base_reply += "\n\nHas your issue been resolved? Please reply Yes or No."
        pending_question = "resolution"
    else:
        pending_question = state.get("pending_question") or ""

    events = _append_event(state, "handle_response -> auto reply")
    history = list(state.get("history") or [])
    history.append({"role": "assistant", "content": base_reply})
    return {
        "response": base_reply,
        "escalated": False,
        "status": status,
        "final_action": final_action,
        "events": events,
        "history": history,
        "pending_question": pending_question,
    }


# 6. Escalation Handover Agent
def escalate(state: State) -> dict:
    """Send fixed escalation message without using the LLM."""
    events = _append_event(state, "escalate -> fixed escalation response")
    response = ESCALATION_REPLY
    history = list(state.get("history") or [])
    history.append({"role": "assistant", "content": response})
    return {
        "response": response,
        "escalated": True,
        "status": "ESCALATED",
        "final_action": "ESCALATE",
        "events": events,
        "history": history,
        "pending_question": "",
        "resolution_no_count": 0,
    }


# ------- Build LangGraph workflow -------

workflow = StateGraph(State)

workflow.add_node("greet", greet)
workflow.add_node("validate_input", validate_input)
workflow.add_node("check_followup", check_followup)
workflow.add_node("detect_negative", detect_negative_turn)
workflow.add_node("detect_human_request", detect_human_request)
workflow.add_node("categorize", categorize)
workflow.add_node("assess_billing_risk", assess_billing_risk)
workflow.add_node("analyze_sentiment", analyze_sentiment)
workflow.add_node("generate_first_round_reply", generate_first_round_reply)
# New add
workflow.add_node("retrieve_rag_context", retrieve_rag_context)
workflow.add_node("decide_escalation", decide_escalation)
workflow.add_node("handle_response", handle_response)
workflow.add_node("escalate", escalate)

# Stage 1: greeting + validation + noise check + understanding + (placeholder) initial reply
workflow.add_edge("greet", "validate_input")
workflow.add_conditional_edges(
    "validate_input",
    route_after_validation,
    {
        "detect_human_request": "detect_human_request",
        "end": END,
    },
)
workflow.add_conditional_edges(
    "detect_negative",
    route_after_negative,
    {
        "escalate": "escalate",
        "check_followup": "check_followup",
        "categorize": "categorize",
    },
)
workflow.add_conditional_edges(
    "detect_human_request",
    route_after_human_request,
    {
        "escalate": "escalate",
        "check_followup": "check_followup",
        "detect_negative": "detect_negative",
    },
)
workflow.add_conditional_edges(
    "categorize",
    route_after_categorize,
    {
        "assess_billing_risk": "assess_billing_risk",
        "retrieve_rag_context": "retrieve_rag_context",  # New add
    },
)
workflow.add_conditional_edges(
    "assess_billing_risk",
    route_after_billing_risk,
    {
        "escalate": "escalate",
        "retrieve_rag_context": "retrieve_rag_context",
    },
)
workflow.add_conditional_edges(
    "check_followup",
    route_after_followup,
    {
        "validate_input": "validate_input",
        "categorize": "categorize",
        "end": END,
    },
)
workflow.add_edge("generate_first_round_reply", "decide_escalation")

# New add
workflow.add_edge("retrieve_rag_context", "generate_first_round_reply")


workflow.add_conditional_edges(
    "decide_escalation",
    route_after_decision,
    {
        "escalate": "escalate",
        "handle_response": "handle_response",
    },
)

workflow.add_edge("handle_response", END)
workflow.add_edge("escalate", END)

workflow.set_entry_point("greet")

app = workflow.compile()


if __name__ == "__main__":
    # Minimal terminal runner for quick testing
    sample_state = {
        "query": "My payment was declined twice today.",
        "resolved": False,
        "wants_human": False,
    }
    result = app.invoke(sample_state)
    print(result)
