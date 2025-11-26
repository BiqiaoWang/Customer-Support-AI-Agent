# ==========================================
# Customer Support Automation RAG Workflow (Using Qdrant VB + Llama-3.1)
# ==========================================

from typing import TypedDict
from langgraph.graph import StateGraph, END
from langchain_core.prompts import ChatPromptTemplate
import os

# ------------------------------------------
# 1️⃣ Define State Dictionary (TypedDict)
# ------------------------------------------
# Each ticket/request stores these states in the workflow
class State(TypedDict):
    query: str             # Customer input text
    category: str          # Classification result: Technical / Billing / General
    sentiment: str         # Sentiment analysis result: Positive / Neutral / Negative
    response: str          # Auto-reply content
    ticket_priority: str   # Priority: Low / Medium / High / Urgent
    escalated: bool        # Whether the ticket needs human intervention
    context: str           # Knowledge retrieved from RAG
    rag_can_answer: bool   # Whether knowledge base information is available for answer

# ------------------------------------------
# 2️⃣ Initialize Hugging Face LLM Client
# ------------------------------------------
# Using Llama-3.1-Instruct model
from huggingface_hub import InferenceClient

MODEL_NAME = "meta-llama/Llama-3.1-8B-Instruct"
client = InferenceClient(
    model=MODEL_NAME,
    token=os.getenv("HF_TOKEN")  # HF Token stored as environment variable
)

# General LLM call function
def llm_chat(system_prompt: str, user_prompt: str, max_tokens: int = 256) -> str:
    """
    Use Llama model for conversational tasks
    system_prompt: system role description
    user_prompt: user input
    max_tokens: output length limit
    """
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]
    completion = client.chat_completion(
        messages=messages,
        max_tokens=max_tokens,
    )
    return completion.choices[0].message["content"]

# ------------------------------------------
# 3️⃣ Load local Excel knowledge base and split into chunks
# ------------------------------------------
from langchain_community.document_loaders import UnstructuredExcelLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

# Load local Excel knowledge base
docs = UnstructuredExcelLoader("your_knowledge.xlsx").load()

# Split into 500-character chunks with 100-character overlap
text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=100)
doc_splits = text_splitter.split_documents(docs)

# ----------------------------------------------
# 4️⃣ Initialize Vector Database (VB)
# ------------------------------------------
# Using Qdrant instead of local FAISS
from langchain_community.vectorstores import Qdrant
from langchain_openai import OpenAIEmbeddings
from qdrant_client import QdrantClient

# Connect to cloud Qdrant service

qdrant_client = QdrantClient(
    url="https://935b80de-2d8b-4e02-930b-7c2c068dcb00.us-east4-0.gcp.cloud.qdrant.io:6333", 
    api_key="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJhY2Nlc3MiOiJtIn0.SaNmBM2Hbkiv3KgMWfMLLlkD5uHdBA4KCEThwWLlsTY",
)

print(qdrant_client.get_collections())

# Vectorize the document chunks and store in Qdrant
vectorstore = Qdrant.from_documents(
    doc_splits,
    embedding=OpenAIEmbeddings(),           # Use OpenAI embeddings to generate vectors
    client=qdrant_client,                   # Specify Qdrant client
    collection_name="support_kb_collection" # Custom collection name
)

# Create retriever for RAG queries
retriever = vectorstore.as_retriever()

# ==========================================
# 5️⃣ Define Workflow Node Functions (for StateGraph)
# ==========================================

# -----------------
# 5.1 Classification Node (categorize)
# -----------------
def categorize(state: State) -> dict:
    """
    Classify customer query as Technical / Billing / General
    """
    system_prompt = (
        "You are a customer support ticket classifier. "
        "Classify each query into ONE of these categories: Technical, Billing, General."
    )
    user_prompt = f"Customer query:\n{state['query']}\n\nOnly answer with one word: Technical, Billing, or General."
    
    category = llm_chat(system_prompt, user_prompt).strip().title()  # Capitalize first letter
    return {"category": category}

# -----------------
# 5.2 Sentiment Analysis Node (analyze_sentiment)
# -----------------
def analyze_sentiment(state: State) -> dict:
    """
    Perform sentiment analysis: Positive / Neutral / Negative
    """
    system_prompt = (
        "You are a sentiment analysis assistant for customer support. "
        "Classify sentiment as Positive, Neutral, or Negative."
    )
    user_prompt = f"Customer query:\n{state['query']}\n\nOnly answer with one word: Positive, Neutral, or Negative."
    
    sentiment = llm_chat(system_prompt, user_prompt).strip().title()
    return {"sentiment": sentiment}

# -----------------
# 5.3 Priority Scoring Node (score_priority)
# -----------------
def score_priority(state: State) -> dict:
    """
    Determine ticket priority based on query, category, and sentiment:
    Low / Medium / High / Urgent
    """
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
    priority = llm_chat(system_prompt, user_prompt).strip().title()
    return {"ticket_priority": priority}

# -----------------
# 5.4 RAG Knowledge Retrieval Node (retrieve_knowledge)
# -----------------
def retrieve_knowledge(state: State) -> dict:
    """
    Retrieve Excel knowledge base content using vector database
    """
    def rag_search(query: str, category: str) -> str:
        # Search query + category combination
        search_query = f"{query} {category}" if category else query
        docs = retriever.get_relevant_documents(search_query)
        if not docs:
            return ""
        # Take top 3 documents as context
        context = "\n\n".join(doc.page_content for doc in docs[:3])
        return context

    context = rag_search(state["query"], state.get("category", ""))
    rag_can_answer = bool(context)  # Whether valid knowledge was retrieved
    return {"context": context, "rag_can_answer": rag_can_answer}

# -----------------
# 5.5 Decide Escalation Node (decide_escalation)
# -----------------
def decide_escalation(state: State) -> dict:
    """
    Decide whether to escalate to human agent based on priority and RAG result
    """
    priority = (state.get("ticket_priority") or "").lower()
    rag_can_answer = state.get("rag_can_answer", False)  # Default False
    escalate_type = "none"

    if priority == "urgent":
        escalate_type = "urgent"
    elif priority == "high":
        escalate_type = "high" if not rag_can_answer else "none"
    elif priority == "medium":
        escalate_type = "medium" if not rag_can_answer else "none"
    elif priority == "low":
        escalate_type = "low" if not rag_can_answer else "none"

    return {"escalated": escalate_type != "none", "escalate_type": escalate_type}

# -----------------
# 5.6 Auto-Reply Node (handle_response)
# -----------------
def handle_response(state: State) -> dict:
    """
    Generate auto-reply based on query, category, sentiment, priority, and RAG context
    """
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
        f"Knowledge context:\n{state.get('context','')}\n"
        f"Customer query:\n{state['query']}"
    )
    response = llm_chat(system_prompt, user_prompt, max_tokens=300)
    return {"response": response}

# -----------------
# 5.7 Human Handover Node (escalate)
# -----------------
def escalate(state: State) -> dict:
    """
    Generate handover note for human agent
    """
    system_prompt = (
        "You are a support assistant preparing a handover note to a human agent. "
        "Summarize the user's issue, sentiment, and priority in a short paragraph. "
        "Make it easy for a human agent to quickly understand and continue."
    )
    user_prompt = (
        f"Category: {state.get('category')}\n"
        f"Sentiment: {state.get('sentiment')}\n"
        f"Priority: {state.get('ticket_priority')}\n"
        f"Escalate type: {state.get('escalate_type')}\n"
        f"Knowledge context:\n{state.get('context','')}\n"
        f"Customer query:\n{state['query']}"
    )
    handover_note = llm_chat(system_prompt, user_prompt, max_tokens=250)
    return {
        "response": handover_note,
        "escalated": True,
    }

# ==========================================
# 6️⃣ Build LangGraph Workflow
# ==========================================
workflow = StateGraph(State)

# Add nodes
workflow.add_node("categorize", categorize)
workflow.add_node("analyze_sentiment", analyze_sentiment)
workflow.add_node("score_priority", score_priority)
workflow.add_node("retrieve_knowledge", retrieve_knowledge)
workflow.add_node("decide_escalation", decide_escalation)
workflow.add_node("handle_response", handle_response)
workflow.add_node("escalate", escalate)

# Add node dependencies
workflow.add_edge("categorize", "analyze_sentiment")
workflow.add_edge("analyze_sentiment", "score_priority")
workflow.add_edge("score_priority", "retrieve_knowledge")
workflow.add_edge("retrieve_knowledge", "decide_escalation")

# Conditional branching function
def route_after_decision(state: State) -> str:
    """
    Choose next node based on decide_escalation result:
    - escalated → escalate node
    - not escalated → handle_response node
    """
    return "escalate" if state.get("escalated") else "handle_response"

workflow.add_conditional_edges(
    "decide_escalation",
    route_after_decision,
    {
        "escalate": "escalate",
        "handle_response": "handle_response",
    },
)

# Automatic termination nodes
workflow.add_edge("handle_response", END)
workflow.add_edge("escalate", END)

# Set entry point
workflow.set_entry_point("categorize")

# Compile workflow1
app = workflow.compile()
