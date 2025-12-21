import sys
from pathlib import Path
from datetime import datetime

import streamlit as st
import pandas as pd

# ==== 路径 & 工作流导入 ====
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))

from src.main_logic import app, GREETING


st.set_page_config(page_title="AI Support Assistant", page_icon="🤖")
st.title("AI Support Assistant")


# ==== 1. 全局 tickets 表，只存“已经完结的工单” ====
if "tickets" not in st.session_state:
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

# 当前工单 ID：只在会话开始时生成一次，用完结状态落一条
if "current_ticket_id" not in st.session_state:
    st.session_state.current_ticket_id = "TICKET-1001"

def _next_ticket_id() -> str:
    """简单递增工单号：TICKET-1001, 1002, ..."""
    if st.session_state.tickets.empty:
        base = 1001
    else:
        # 取最后一行的数字部分 + 1
        last_id = st.session_state.tickets.iloc[-1]["ID"]
        try:
            base = int(str(last_id).split("-")[-1]) + 1
        except Exception:
            base = 1001
    return f"TICKET-{base}"


# ==== 2. 对话状态 ====
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


# ==== 3. 渲染历史 ====
for msg in state.get("history", []):
    role = msg.get("role", "assistant")
    content = msg.get("content", "")
    with st.chat_message("assistant" if role == "assistant" else "user"):
        st.markdown(content)

st.caption(f"Current ticket ID: {ticket_id}")


# ==== 4. 结束状态处理：此时才写入 tickets 表 ====
status_flag = (state.get("status") or "").upper()
if status_flag in {"CLOSED", "ESCALATED"}:
    msg = (
        "This ticket is closed."
        if status_flag == "CLOSED"
        else "This ticket has been escalated to a human agent."
    )
    st.info(msg)

    # 只在还没落表时写一次（避免重复插入）
    # 简单判断：当前 ticket_id 是否已经在 tickets 里存在
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



    # ==== 新增：把完整对话 state 保存到 ticket_details ====
    if "ticket_details" not in st.session_state:
        st.session_state.ticket_details = {}

    # 只在第一次保存，避免重复覆盖；如果希望总是以最新为准，可以去掉这个 if
    if ticket_id not in st.session_state.ticket_details:
        st.session_state.ticket_details[ticket_id] = {
            "state": state,
            "history": state.get("history", []),
            "events": state.get("events", []),
        }

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
    with st.expander("Tickets (debug)"):
        st.dataframe(st.session_state.tickets, use_container_width=True)
    st.stop()


# ==== 5. 非结束状态：正常对话 ====
pending = state.get("pending_question") or ""
yesno_pending = pending in {"resolution", "escalation"}
prompt_value = None

if yesno_pending:
    st.markdown("**Please choose an option:**")
    col1, col2 = st.columns(2)
    with col1:
        yes_clicked = st.button("Yes", key=f"yes_{pending}")
    with col2:
        no_clicked = st.button("No", key=f"no_{pending}")
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
        "Describe your issue (<= 200 chars, English letters/numbers/punctuation/spaces)."
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
        with st.chat_message("user"):
            st.markdown(prompt_value)

        wait_placeholder = st.empty()
        with wait_placeholder.chat_message("assistant"):
            st.markdown("Please wait a moment, thank you for your patience.")

        result = app.invoke(base_state)

        st.session_state.state = result
        st.rerun()

    except Exception as exc:
        st.error(f"Error: {exc}")
        st.stop()


with st.expander("State (debug)"):
    st.json(st.session_state.state)
with st.expander("Tickets (debug)"):
    st.dataframe(st.session_state.tickets, use_container_width=True)
