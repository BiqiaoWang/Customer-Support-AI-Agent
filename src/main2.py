from typing import TypedDict
from langgraph.graph import StateGraph, END

import os
from huggingface_hub import InferenceClient


class State(TypedDict):
    # Original customer ticket text
    query: str

    # Stage 1: automatic understanding
    ticket_type: str          # e.g. "Technical", "Billing", "General"
    sentiment: str            # e.g. "Positive", "Neutral", "Negative"
    ticket_priority: str      # e.g. "Low", "Medium", "High", "Urgent"

    # Stage 1: automatic reply (to be filled by RAG agent)
    initial_reply: str        # reply generated from enterprise knowledge base / RAG

    # Stage 2: follow-up from the customer / UI
    user_feedback: str        # free-text feedback, e.g. "No, it is not fixed"
    resolved: bool            # did the customer confirm the issue is resolved?
    wants_human: bool         # did the customer clearly request a human agent?

    # Final decision & output
    escalated: bool           # whether this ticket should be escalated to a human
    response: str             # final reply to customer OR handover note


MODEL_NAME = "meta-llama/Llama-3.1-8B-Instruct"

client = InferenceClient(
    model=MODEL_NAME,
    token=os.getenv("HF_TOKEN"),
)


def llm_chat(system_prompt: str, user_prompt: str, max_tokens: int = 256) -> str:
    """Simple helper around the HF Inference Client."""

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]

    completion = client.chat_completion(
        messages=messages,
        max_tokens=max_tokens,
    )

    # NOTE: API response format may differ slightly depending on the client version.
    return completion.choices[0].message["content"]


# 1. Classifier Agent
def categorize(state: State) -> dict:
    """Classify the ticket into a high-level ticket_type.

    This is the first step of the workflow and writes only `ticket_type`
    into the shared state.
    """
    system_prompt = (
        "You are a customer support ticket classifier. "
        "Classify each query into ONE of these categories: "
        "Technical, Billing, General."
    )
    user_prompt = (
        f"Customer query:\n{state['query']}\n\n"
        "Only answer with one word: Technical, Billing, or General."
    )

    ticket_type = llm_chat(system_prompt, user_prompt).strip()
    return {"ticket_type": ticket_type}


# 2. Sentiment Agent
def analyze_sentiment(state: State) -> dict:
    """Sentiment analysis for the current ticket."""
    system_prompt = (
        "You are a sentiment analysis assistant for customer support. "
        "Classify sentiment as Positive, Neutral, or Negative."
    )
    user_prompt = (
        f"Customer query:\n{state['query']}\n\n"
        "Only answer with one word: Positive, Neutral, or Negative."
    )

    sentiment = llm_chat(system_prompt, user_prompt).strip()
    return {"sentiment": sentiment}



# 3. Initial Reply Agent (RAG placeholder)
def generate_initial_reply(state: State) -> dict:
    """Generate the *first round* automatic reply.

    ✅ IMPORTANT: The RAG logic (retrieval from company KB, FAQ, etc.)
    is NOT implemented here because it is handled by another teammate.

    This function only defines the place in the workflow where the RAG
    agent will plug in and ensures that each agent updates its own field.

    For now, we simply keep any existing `initial_reply` value or use
    an empty string as a placeholder so that the graph can still run.
    """

    initial_reply = state.get("initial_reply") or ""
    return {"initial_reply": initial_reply}


# 4. Escalation Decision Agent
def decide_escalation(state: State) -> dict:
    """Decide whether this ticket should be escalated to a human agent.

    The decision is based on:
      • ticket_type (e.g. transaction / billing related)
      • sentiment polarity
      • explicit user request for a human
      • whether the user has already confirmed the issue is resolved
    """
    ticket_type = (state.get("ticket_type") or "").lower()
    sentiment = (state.get("sentiment") or "").lower()
    priority = (state.get("ticket_priority") or "").lower()

    resolved = bool(state.get("resolved", False))
    wants_human = bool(state.get("wants_human", False))

    # --- Example rule set, matching the narrative logic ---

    # If the customer already confirmed it's resolved, do NOT escalate.
    if resolved:
        return {"escalated": False}

    # 1) Certain ticket types (e.g. billing / transaction) are more sensitive.
    if ticket_type in ["billing", "transaction"]:
        return {"escalated": True}

    # 2) Always respect a clear request for human support.
    if wants_human:
        return {"escalated": True}

    # 3) Escalate if the customer is unhappy and the case seems urgent / high-risk.
    if sentiment == "negative" and priority in ["high", "urgent"]:
        return {"escalated": True}

    # Otherwise, keep it in the automated flow.
    return {"escalated": False}


# 5. Final Response Agent (for non-escalated tickets)
def handle_response(state: State) -> dict:
    """Prepare the final reply to the customer when we do NOT escalate.

    In this workflow design, the actual content of the first reply should
    come from the RAG agent (enterprise knowledge base). Here we simply
    reuse `initial_reply` as the final response, and optionally add a
    gentle follow-up sentence.
    """
    base_reply = state.get("initial_reply") or (
        "Thank you for your message. "
        "Our automated system could not generate an answer yet."
    )

    # If we know it is not resolved, encourage the user to ask for a human.
    resolved = bool(state.get("resolved", False))
    if not resolved:
        base_reply += (
            "\n\nIf this does not fully solve your issue, you can request "
            "to be transferred to a human support agent."
        )

    return {
        "response": base_reply,
        "escalated": False,
    }


# 6. Escalation Handover Agent
def escalate(state: State) -> dict:
    """Prepare a concise handover note for a human agent."""
    system_prompt = (
        "You are a support assistant preparing a handover note to a human agent. "
        "Summarize the user's issue, sentiment, and priority in a short paragraph. "
        "Make it easy for a human agent to quickly understand and continue."
    )
    user_prompt = (
        f"Ticket type: {state.get('ticket_type')}\n"
        f"Sentiment: {state.get('sentiment')}\n"
        f"Priority: {state.get('ticket_priority')}\n"
        f"Customer query:\n{state['query']}"
    )

    handover_note = llm_chat(system_prompt, user_prompt, max_tokens=250)

    return {
        # This `response` is now a handover summary, not a user-facing answer.
        "response": handover_note,
        "escalated": True,
    }


# ------- Build LangGraph workflow -------

workflow = StateGraph(State)

workflow.add_node("categorize", categorize)
workflow.add_node("analyze_sentiment", analyze_sentiment)
workflow.add_node("score_priority", score_priority)
workflow.add_node("generate_initial_reply", generate_initial_reply)
workflow.add_node("decide_escalation", decide_escalation)
workflow.add_node("handle_response", handle_response)
workflow.add_node("escalate", escalate)

# Stage 1: understanding + (placeholder) initial reply
workflow.add_edge("categorize", "analyze_sentiment")
workflow.add_edge("analyze_sentiment", "score_priority")
workflow.add_edge("score_priority", "generate_initial_reply")
workflow.add_edge("generate_initial_reply", "decide_escalation")


def route_after_decision(state: State) -> str:
    """Router: after the decision node, choose the next step."""
    return "escalate" if state.get("escalated") else "handle_response"


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

workflow.set_entry_point("categorize")

app = workflow.compile()