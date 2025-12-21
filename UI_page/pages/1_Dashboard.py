import streamlit as st
import altair as alt
import pandas as pd

st.title("Ticket Dashboard")

# 1. 确认 Workspace 已经写入过工单
if "tickets" not in st.session_state or st.session_state.tickets.empty:
    st.warning("还没有工单，请先在 Workspace 页面创建一条。")
    st.stop()

df = st.session_state.tickets

# 2. 上半部分：历史工单表
st.subheader("History Tickets")
st.dataframe(df, use_container_width=True)

# 3. 下半部分：左侧 KPI，右侧两个图（先做简单版）
st.subheader("Support Ticket Analytics")

left, right = st.columns([1, 2])

with left:
    st.write("关键指标（示例，占位）")
    # 真实逻辑以后再根据 df 来算，这里先用简单示例
    new_today = len(df[df["Created Time"] == df["Created Time"].max()])
    escalation_rate = (df["Escalation Needed"] == "Yes").mean() if not df.empty else 0.0
    auto_resolved_rate = 1 - escalation_rate if not df.empty else 0.0

    st.metric("New tickets today", new_today)
    st.metric("Auto‑resolution rate", f"{auto_resolved_rate*100:.0f}%")
    st.metric("Escalation rate", f"{escalation_rate*100:.0f}%")

with right:
    c1, c2 = st.columns(2)

    with c1:
        st.write("Sentiment Distribution Over Time")

        # 为了避免一开始没数据出错，简单做个占位逻辑
        if not df.empty:
            # 用 Created Time + Sentiment 做一个计数柱状图
            chart_data = (
                df.groupby(["Created Time", "Sentiment"])
                .size()
                .reset_index(name="count")
            )
            chart1 = (
                alt.Chart(chart_data)
                .mark_bar()
                .encode(
                    x="Created Time:O",
                    y="count:Q",
                    color="Sentiment:N",
                )
                .properties(height=250)
            )
            st.altair_chart(chart1, use_container_width=True)
        else:
            st.info("暂无数据。")

    with c2:
        st.write("Ticket Type Distribution")

        if not df.empty:
            type_data = (
                df.groupby("Type")
                .size()
                .reset_index(name="count")
            )
            chart2 = (
                alt.Chart(type_data)
                .mark_arc()
                .encode(
                    theta="count:Q",
                    color="Type:N",
                )
                .properties(height=250)
            )
            st.altair_chart(chart2, use_container_width=True)
        else:
            st.info("暂无数据。")
