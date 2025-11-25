# ==========================================
# 客服自动化 RAG 流程（使用 Qdrant VB + Llama-3.1）
# ==========================================

from typing import TypedDict
from langgraph.graph import StateGraph, END
from langchain_core.prompts import ChatPromptTemplate
import os

# ------------------------------------------
# 1️⃣ 定义状态字典（TypedDict）
# ------------------------------------------
# 每个 ticket/请求在流程中需要的状态
class State(TypedDict):
    query: str             # 客户输入的文本
    category: str          # 分类结果：Technical / Billing / General
    sentiment: str         # 情感分析结果：Positive / Neutral / Negative
    response: str          # 自动回复内容
    ticket_priority: str   # 优先级：Low / Medium / High / Urgent
    escalated: bool        # 是否需要人工处理
    context: str           # RAG 检索到的知识库内容
    rag_can_answer: bool   # 是否有知识库信息可用于回答

# ------------------------------------------
# 2️⃣ 初始化 Hugging Face LLM 客户端
# ------------------------------------------
# 使用 Llama-3.1-Instruct 模型
from huggingface_hub import InferenceClient

MODEL_NAME = "meta-llama/Llama-3.1-8B-Instruct"
client = InferenceClient(
    model=MODEL_NAME,
    token=os.getenv("HF_TOKEN")  # 环境变量中存放 HF Token
)

# 通用 LLM 调用函数
def llm_chat(system_prompt: str, user_prompt: str, max_tokens: int = 256) -> str:
    """
    使用 Llama 模型完成对话式任务
    system_prompt: 系统角色描述
    user_prompt: 用户输入
    max_tokens: 输出长度限制
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
# 3️⃣ 加载本地 Excel 知识库，并拆分成块
# ------------------------------------------
from langchain_community.document_loaders import UnstructuredExcelLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

# 加载知识库 Excel 文件（本地路径）
docs = UnstructuredExcelLoader("your_knowledge.xlsx").load()

# 拆分成 500 字的文本块，每块有 100 字重叠
text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=100)
doc_splits = text_splitter.split_documents(docs)

# ------------------------------------------
# 4️⃣ 初始化向量数据库（Vector Database, VB）
# ------------------------------------------
# 使用 Qdrant 作为向量数据库，替代本地 FAISS
from langchain_community.vectorstores import Qdrant
from langchain_openai import OpenAIEmbeddings
from qdrant_client import QdrantClient

# 连接本地 Qdrant 服务
qdrant_client = QdrantClient(host="localhost", port=6333)

# 将拆分后的文档向量化并存入 Qdrant
vectorstore = Qdrant.from_documents(
    doc_splits,
    embedding=OpenAIEmbeddings(),           # OpenAI Embeddings 生成向量
    client=qdrant_client,                   # 指定 Qdrant 客户端
    collection_name="support_kb_collection" # 自定义 collection 名称
)

# 创建检索器，用于后续 RAG 查询
retriever = vectorstore.as_retriever()

# ==========================================
# 5️⃣ 各功能节点函数定义（用于 StateGraph）
# ==========================================

# -----------------
# 5.1 分类节点（categorize）
# -----------------
def categorize(state: State) -> dict:
    """
    将客户查询分类为 Technical / Billing / General
    """
    system_prompt = (
        "You are a customer support ticket classifier. "
        "Classify each query into ONE of these categories: Technical, Billing, General."
    )
    user_prompt = f"Customer query:\n{state['query']}\n\nOnly answer with one word: Technical, Billing, or General."
    
    category = llm_chat(system_prompt, user_prompt).strip().title()  # 标准化首字母大写
    return {"category": category}

# -----------------
# 5.2 情感分析节点（analyze_sentiment）
# -----------------
def analyze_sentiment(state: State) -> dict:
    """
    对客户查询进行情感分析：Positive / Neutral / Negative
    """
    system_prompt = (
        "You are a sentiment analysis assistant for customer support. "
        "Classify sentiment as Positive, Neutral, or Negative."
    )
    user_prompt = f"Customer query:\n{state['query']}\n\nOnly answer with one word: Positive, Neutral, or Negative."
    
    sentiment = llm_chat(system_prompt, user_prompt).strip().title()
    return {"sentiment": sentiment}

# -----------------
# 5.3 优先级评分节点（score_priority）
# -----------------
def score_priority(state: State) -> dict:
    """
    根据查询内容、分类和情感分析结果决定工单优先级：
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
# 5.4 RAG 知识检索节点（retrieve_knowledge）
# -----------------
def retrieve_knowledge(state: State) -> dict:
    """
    使用向量数据库检索 Excel 文档内容，生成知识上下文
    """
    def rag_search(query: str, category: str) -> str:
        # 搜索 query + category 组合
        search_query = f"{query} {category}" if category else query
        docs = retriever.get_relevant_documents(search_query)
        if not docs:
            return ""
        # 取前 3 个文档作为上下文
        context = "\n\n".join(doc.page_content for doc in docs[:3])
        return context

    context = rag_search(state["query"], state.get("category", ""))
    rag_can_answer = bool(context)  # 是否检索到有效知识
    return {"context": context, "rag_can_answer": rag_can_answer}

# -----------------
# 5.5 决定是否升级人工节点（decide_escalation）
# -----------------
def decide_escalation(state: State) -> dict:
    """
    根据优先级和是否有知识库答案决定是否升级给人工
    """
    priority = (state.get("ticket_priority") or "").lower()
    rag_can_answer = state.get("rag_can_answer", False)  # 默认 False，防止误判
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
# 5.6 自动回复节点（handle_response）
# -----------------
def handle_response(state: State) -> dict:
    """
    基于查询、分类、情感、优先级和 RAG 上下文生成自动回复
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
# 5.7 人工交接节点（escalate）
# -----------------
def escalate(state: State) -> dict:
    """
    生成给人工客服的交接信息
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
# 6️⃣ 构建 LangGraph 流程
# ==========================================
workflow = StateGraph(State)

# 添加节点
workflow.add_node("categorize", categorize)
workflow.add_node("analyze_sentiment", analyze_sentiment)
workflow.add_node("score_priority", score_priority)
workflow.add_node("retrieve_knowledge", retrieve_knowledge)
workflow.add_node("decide_escalation", decide_escalation)
workflow.add_node("handle_response", handle_response)
workflow.add_node("escalate", escalate)

# 添加节点依赖关系
workflow.add_edge("categorize", "analyze_sentiment")
workflow.add_edge("analyze_sentiment", "score_priority")
workflow.add_edge("score_priority", "retrieve_knowledge")
workflow.add_edge("retrieve_knowledge", "decide_escalation")

# 条件分流函数
def route_after_decision(state: State) -> str:
    """
    根据 decide_escalation 的结果选择下一步：
    - escalated → escalate 节点
    - 未升级 → handle_response 节点
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

# 自动终止节点
workflow.add_edge("handle_response", END)
workflow.add_edge("escalate", END)

# 设置入口
workflow.set_entry_point("categorize")

# 编译流程
app = workflow.compile()
