from typing import TypedDict
from langgraph.graph import StateGraph, END
from langchain_core.prompts import ChatPromptTemplate

class State(TypedDict):
    query: str
    category: str
    sentiment: str
    response: str
    ticket_priority: str
    escalated: bool

import os
from huggingface_hub import InferenceClient

MODEL_NAME = "meta-llama/Llama-3.1-8B-Instruct"

client = InferenceClient(
    model=MODEL_NAME,
    token=os.getenv("HF_TOKEN")
)

def llm_chat(system_prompt: str, user_prompt: str, max_tokens: int = 256) -> str:

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]

    completion = client.chat_completion(
        messages=messages,
        max_tokens=max_tokens,
    )

    return completion.choices[0].message["content"]

# 1. Classifier Agent
def categorize(state: State) -> dict:
    system_prompt = (
        "You are a customer support ticket classifier. "
        "Classify each query into ONE of these categories: "
        "Technical, Billing, General."
    )
    user_prompt = (
        f"Customer query:\n{state['query']}\n\n"
        "Only answer with one word: Technical, Billing, or General."
    )

    category = llm_chat(system_prompt, user_prompt).strip()
    return {"category": category}


# 2. Sentiment Agent
def analyze_sentiment(state: State) -> dict:
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


# 3. Priority Agent
def score_priority(state: State) -> dict:
    system_prompt = (
        "You are a customer support ticket priority scorer. "
        "Given the user query, ticket category and sentiment, "
        "decide the ticket priority as one of: Low, Medium, High, Urgent."
    )
    user_prompt = (
        f"Category: {state.get('category')}\n"
        f"Sentiment: {state.get('sentiment')}\n"
        f"Customer query:\n{state['query']}\n\n"
        "Only answer with one word: Low, Medium, High, or Urgent."
    )

    priority = llm_chat(system_prompt, user_prompt).strip()
    return {"ticket_priority": priority}


# 4. Escalation Agent
def decide_escalation(state: State) -> dict:

    sentiment = (state.get("sentiment") or "").lower()
    priority = (state.get("ticket_priority") or "").lower()

    should_escalate = (
        sentiment == "negative"
        and priority in ["high", "urgent"]
    )

    return {"escalated": should_escalate}


# 5. Response Agent
def handle_response(state: State) -> dict:
    system_prompt = (
        "You are a helpful customer support agent. "
        "Write a clear, polite reply to the user.\n"
        "You know the ticket category, sentiment, and priority.\n"
        "Do NOT mention that you are an AI model."
    )
    user_prompt = (
        f"Category: {state.get('category')}\n"
        f"Sentiment: {state.get('sentiment')}\n"
        f"Priority: {state.get('ticket_priority')}\n"
        f"Customer query:\n{state['query']}"
    )

    response = llm_chat(system_prompt, user_prompt, max_tokens=300)
    return {"response": response}


# 6. Escalation Agent
def escalate(state: State) -> dict:
    system_prompt = (
        "You are a support assistant preparing a handover note to a human agent. "
        "Summarize the user's issue, sentiment, and priority in a short paragraph. "
        "Make it easy for a human agent to quickly understand and continue."
    )
    user_prompt = (
        f"Category: {state.get('category')}\n"
        f"Sentiment: {state.get('sentiment')}\n"
        f"Priority: {state.get('ticket_priority')}\n"
        f"Customer query:\n{state['query']}"
    )

    handover_note = llm_chat(system_prompt, user_prompt, max_tokens=250)


    return {
        "response": handover_note,  
        "escalated": True,
    }

# ------- Build LangGraph workflow -------

workflow = StateGraph(State)


workflow.add_node("categorize", categorize)
workflow.add_node("analyze_sentiment", analyze_sentiment)
workflow.add_node("score_priority", score_priority)
workflow.add_node("decide_escalation", decide_escalation)
workflow.add_node("handle_response", handle_response)
workflow.add_node("escalate", escalate)


workflow.add_edge("categorize", "analyze_sentiment")
workflow.add_edge("analyze_sentiment", "score_priority")
workflow.add_edge("score_priority", "decide_escalation")



def route_after_decision(state: State) -> str:
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




