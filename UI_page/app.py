import sys
from pathlib import Path
from datetime import datetime
import json
import sqlite3

import streamlit as st
import pandas as pd

# ==== 路径 & 工作流导入 ====
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))

from src.main_logic_rag_Russell import app, GREETING

# ==== SQLite: 路径 & 工具函数 ====
DB_PATH = ROOT / "tickets.db"


def get_connection():
    return sqlite3.connect(DB_PATH)


def init_db():
    conn = get_connection()
    cur = conn.cursor()
    # 概览表：Dashboard 用
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS tickets (
            id TEXT PRIMARY KEY,
            created_time TEXT,
            status TEXT,
            type TEXT,
            sentiment TEXT,
            escalation_needed INTEGER
        )
        """
    )
    # 详情表：完整 state 存 JSON
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS ticket_details (
            ticket_id TEXT PRIMARY KEY,
            state_json TEXT
        )
        """
    )
    conn.commit()
    conn.close()


# 初始化数据库（如果已有表就什么也不做）
init_db()

st.set_page_config(page_title="AI Support Assistant", page_icon="🤖")

# 全局轻量样式：按钮 + 气泡字体
st.markdown(
    """
    <style>
    .stButton>button {
        border-radius: 999px;
        border: none;
        background: #4c6fff;
        color: white;
        padding: 0.35rem 1.2rem;
        font-weight: 500;
    }
    .stButton>button:hover {
        background: #3b57d0;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.title("AI Support Assistant")

# ==== 1. 从 SQLite 恢复 tickets 表（如果有），否则创建空表 ====
if "tickets" not in st.session_state:
    conn = get_connection()
    try:
        df = pd.read_sql("SELECT * FROM tickets", conn)
        # 和原来的列名保持一致
        df = df.rename(
            columns={
                "id": "ID",
                "created_time": "Created Time",
                "status": "Status",
                "type": "Type",
                "sentiment": "Sentiment",
                "escalation_needed": "Escalation Needed",
            }
        )
        # 把 0/1 转成 Yes/No，方便和原 UI 对齐
        if not df.empty:
            df["Escalation Needed"] = df["Escalation Needed"].apply(
                lambda x: "Yes" if int(x) == 1 else "No"
            )
        st.session_state.tickets = df
    except Exception:
        st.session_state.tickets = pd.DataFrame(
            columns=[
                "ID",
                "Created Time",
                "Status",
                "Type",
                "Sentiment",
                "Escalation Needed",
            ]
        )
    finally:
        conn.close()

# 当前工单 ID：只在会话开始时生成一次，用完结状态落一条
if "current_ticket_id" not in st.session_state:
    df = st.session_state.tickets
    if df.empty:
        base = 1001
    else:
        last_id = df.iloc[-1]["ID"]
        try:
            base = int(str(last_id).split("-")[-1]) + 1
        except Exception:
            base = 1001
    st.session_state.current_ticket_id = f"TICKET-{base}"


def _next_ticket_id() -> str:
    """简单递增工单号：TICKET-1001, 1002, ..."""
    df = st.session_state.tickets
    if df.empty:
        base = 1001
    else:
        last_id = df.iloc[-1]["ID"]
        try:
            base = int(str(last_id).split("-")[-1]) + 1
        except Exception:
            base = 1001
    return f"TICKET-{base}"


# ==== 2. 从 SQLite 恢复 ticket_details（如果有），否则空 dict ====
if "ticket_details" not in st.session_state:
    st.session_state.ticket_details = {}
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("SELECT ticket_id, state_json FROM ticket_details")
        rows = cur.fetchall()
        for tid, state_json in rows:
            try:
                s = json.loads(state_json)
            except Exception:
                continue
            st.session_state.ticket_details[tid] = {
                "state": s,
                "history": s.get("history", []),
                "events": s.get("events", []),
            }
    finally:
        conn.close()

# ==== 3. 对话状态 ====
if "state" not in st.session_state:
    st.session_state.state = {
        "history": [{"role": "assistant", "content": GREETING}],
        "response": GREETING,
        "status": "NEW",
        "events": [],
        "turn": 1,
        "pending_question": "",
        "resolution_no_count": 0,
        "input_valid": True,
        "input_meaningful": True,
        "input_continue": True,
        "restart_to_validate": False,
    }

state = st.session_state.state
ticket_id = st.session_state.current_ticket_id

# ==== 4. 渲染历史：自定义左右气泡 + emoji 头像 ====
for msg in state.get("history", []):
    role = msg.get("role", "assistant")
    content = msg.get("content", "")

    is_assistant = (role == "assistant")
    align = "flex-start" if is_assistant else "flex-end"
    bg = "#f5f6fa" if is_assistant else "#e8f4ff"
    avatar = "🤖" if is_assistant else "🙂"
    avatar_bg = "#ffb648" if is_assistant else "#ff6b6b"

    st.markdown(
        f"""
        <div style="display:flex; justify-content:{align}; margin:8px 0;">
          <div style="display:flex; gap:8px; align-items:flex-start;
                      flex-direction:{'row' if is_assistant else 'row-reverse'};">
            <div style="
                width:32px; height:32px;
                border-radius:12px;
                background:{avatar_bg};
                display:flex; align-items:center; justify-content:center;
                font-size:18px;
            ">
              {avatar}
            </div>
            <div style="
                max-width:70%;
                background:{bg};
                padding:10px 14px;
                border-radius:14px;
                font-size:14px;
                line-height:1.5;
            ">
              {content}
            </div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

st.caption(f"Current ticket ID: {ticket_id}")


# ==== 5. 结束状态处理：此时才写入 tickets 表 & SQLite ====
status_flag = (state.get("status") or "").upper()
if status_flag in {"CLOSED", "ESCALATED"}:
    msg = (
        "This ticket is closed."
        if status_flag == "CLOSED"
        else "This ticket has been escalated to a human agent."
    )
    st.info(msg)

    df = st.session_state.tickets
    if ticket_id not in df["ID"].tolist():
        ticket_type = state.get("ticket_type", "General")
        sentiment = state.get("sentiment", "Non-Negative")
        escalated = bool(state.get("escalated", False))

        new_row = {
            "ID": ticket_id,
            "Created Time": datetime.now().strftime("%m-%d-%Y"),
            "Status": status_flag,
            "Type": ticket_type,
            "Sentiment": sentiment,
            "Escalation Needed": "Yes" if escalated else "No",
        }
        st.session_state.tickets = pd.concat(
            [df, pd.DataFrame([new_row])],
            ignore_index=True,
        )

        # === 写入 SQLite 概览表 ===
        conn = get_connection()
        cur = conn.cursor()
        cur.execute(
            """
            INSERT OR REPLACE INTO tickets
            (id, created_time, status, type, sentiment, escalation_needed)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                ticket_id,
                new_row["Created Time"],
                new_row["Status"],
                new_row["Type"],
                new_row["Sentiment"],
                1 if escalated else 0,
            ),
        )
        conn.commit()
        conn.close()

    # ==== 保存完整对话 state 到 ticket_details（内存） ====
    if "ticket_details" not in st.session_state:
        st.session_state.ticket_details = {}

    if ticket_id not in st.session_state.ticket_details:
        st.session_state.ticket_details[ticket_id] = {
            "state": state,
            "history": state.get("history", []),
            "events": state.get("events", []),
        }

    # === 写入 SQLite 详情表 ===
    conn = get_connection()
    cur = conn.cursor()
    state_json = json.dumps(state, ensure_ascii=False)
    cur.execute(
        """
        INSERT OR REPLACE INTO ticket_details
        (ticket_id, state_json)
        VALUES (?, ?)
        """,
        (ticket_id, state_json),
    )
    conn.commit()
    conn.close()

    # 允许开启一个全新工单（新的对话 + 新的 ticket_id）
    if st.button("Start a new ticket"):
        st.session_state.state = {
            "history": [{"role": "assistant", "content": GREETING}],
            "response": GREETING,
            "status": "NEW",
            "events": [],
            "turn": 1,
            "pending_question": "",
            "resolution_no_count": 0,
            "input_valid": True,
            "input_meaningful": True,
            "input_continue": True,
            "restart_to_validate": False,
        }
        st.session_state.current_ticket_id = _next_ticket_id()
        st.rerun()

    with st.expander("State (debug)"):
        st.json(state)
    st.stop()

# ==== 6. 非结束状态：正常对话 ====
pending = state.get("pending_question") or ""
yesno_pending = pending in {"resolution", "escalation"}
prompt_value = None

if yesno_pending:
    st.markdown("**Please choose an option:**")
    col1, col2 = st.columns(2)
    with col1:
        yes_clicked = st.button("✅ Yes", key=f"yes_{pending}")
    with col2:
        no_clicked = st.button("✖️ No", key=f"no_{pending}")
    if yes_clicked:
        prompt_value = "Yes"
    elif no_clicked:
        prompt_value = "No"
    st.chat_input(
        "Awaiting your selection above (Yes/No).",
        disabled=True,
        key="chat_disabled",
    )
else:
    prompt_value = st.chat_input(
        "Describe your issue, and I’ll help you step by step."
    )


if prompt_value:
    base_state = {k: v for k, v in state.items() if k != "query"}
    base_state.update(
        {
            "query": prompt_value,
            "resolved": False,
            "wants_human": False,
        }
    )

    try:
        # 右侧用户气泡 + emoji 头像
        st.markdown(
            f"""
            <div style="display:flex; justify-content:flex-end; margin:8px 0;">
              <div style="display:flex; gap:8px; align-items:flex-start; flex-direction:row-reverse;">
                <div style="
                    width:32px; height:32px;
                    border-radius:12px;
                    background:#ff6b6b;
                    display:flex; align-items:center; justify-content:center;
                    font-size:18px;
                ">
                  🙂 
                </div>
                <div style="
                    max-width:70%;
                    background:#e8f4ff;
                    padding:10px 14px;
                    border-radius:14px;
                    font-size:14px;
                    line-height:1.5;
                ">
                  {prompt_value}
                </div>
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # 左侧助手“正在思考”气泡
        wait_placeholder = st.empty()
        with wait_placeholder:
            st.markdown(
                """
                <div style="display:flex; justify-content:flex-start; margin:8px 0;">
                  <div style="display:flex; gap:8px; align-items:flex-start;">
                    <div style="
                        width:32px; height:32px;
                        border-radius:12px;
                        background:#ffb648;
                        display:flex; align-items:center; justify-content:center;
                        font-size:18px;
                    ">
                      🤖
                    </div>
                    <div style="
                        max-width:70%;
                        background:#f5f6fa;
                        padding:10px 14px;
                        border-radius:14px;
                        font-size:14px;
                        line-height:1.5;
                    ">
                      Please wait a moment, thank you for your patience.
                    </div>
                  </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        result = app.invoke(base_state)
        st.session_state.state = result
        st.rerun()

    except Exception as exc:
        st.error(f"Error: {exc}")
        st.stop()





with st.expander("State (debug)"):
    st.json(st.session_state.state)

