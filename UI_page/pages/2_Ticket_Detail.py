import streamlit as st
import pandas as pd

st.title("Ticket Detail")

# 1. 确认有工单数据
if "tickets" not in st.session_state or st.session_state.tickets.empty:
    st.warning("还没有工单，请先在 Workspace 页面创建一条。")
    st.stop()

df = st.session_state.tickets

# 2. 选择工单 ID
ticket_id = st.selectbox("选择要查看的工单 ID", options=df["ID"].tolist())

ticket_row = df[df["ID"] == ticket_id]

if ticket_row.empty:
    st.error("找不到这个工单。")
    st.stop()

# 3. 展示该工单的基础信息
st.subheader("工单基本信息")
st.dataframe(ticket_row, use_container_width=True)

# 4. 对话 / 处理历史
st.subheader("对话 / 处理历史")

details_store = st.session_state.get("ticket_details", {})
details = details_store.get(ticket_id)

if not details:
    st.info("当前工单还没有保存对话历史（可能是早期测试工单）。")
else:
    history = details.get("history", [])
    events = details.get("events", [])

    st.markdown("**Conversation history**")
    for msg in history:
        role = msg.get("role", "assistant")
        content = msg.get("content", "")
        with st.chat_message("assistant" if role == "assistant" else "user"):
            st.markdown(content)

    st.markdown("**Event log**")
    for e in events:
        st.write(f"- {e}")
