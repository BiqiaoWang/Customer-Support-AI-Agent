import streamlit as st
import altair as alt
import pandas as pd
import datetime as dt

# 让页面变宽铺满
st.set_page_config(layout="wide")

# 全局轻量样式：字体颜色、表头、标题
st.markdown(
    """
    <style>
    body, .stMarkdown, .stText, .stMetric label {
        color: #333333;
    }
    .stDataFrame thead tr th {
        background-color: #f5f6fa;
        font-weight: 600;
        color: #4a4a4a;
        border-bottom: 1px solid #e1e4eb;
    }
    .stDataFrame tbody tr:hover {
        background-color: #fafbff;
    }
    h1, h2, h3 {
        font-weight: 700;
        color: #222222;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.title("Ticket Dashboard")

# 1. Check tickets
if "tickets" not in st.session_state or st.session_state.tickets.empty:
    st.warning("No tickets yet. Please create one in the Workspace page.")
    st.stop()

df = st.session_state.tickets.copy()

# --- Convert date column (internal use only) ---
df["Created Date"] = pd.to_datetime(
    df["Created Time"], format="%m-%d-%Y", errors="coerce"
).dt.date

# 2. Date filter (affects everything below)
st.subheader("Filters")
col_from, col_to = st.columns(2)
with col_from:
    start_date = st.date_input(
        "From",
        value=df["Created Date"].min() if not df.empty else dt.date.today(),
    )
with col_to:
    end_date = st.date_input(
        "To",
        value=df["Created Date"].max() if not df.empty else dt.date.today(),
    )

mask = (df["Created Date"] >= start_date) & (df["Created Date"] <= end_date)
df_filtered = df[mask].copy()

# 3. Top 5 history table
st.subheader("History Tickets")



df_sorted = df_filtered.sort_values(
    by=["Created Date", "ID"], ascending=[False, False]
)

# 只展示一个时间字段（这里保留 Created Time）
cols_to_show = [
    "ID",
    "Created Time",
    "Status",
    "Type",
    "Sentiment",
    "Escalation Needed",
]
table_data = df_sorted[cols_to_show]

# 高度固定，内容多了在表格内部滚动
st.dataframe(table_data, use_container_width=True, height=220)


# 4. KPIs
st.subheader("Support Ticket Analytics")

kpi1, kpi2, kpi3 = st.columns(3)

new_in_range = len(
    df_filtered[df_filtered["Created Date"] == df_filtered["Created Date"].max()]
)
escalation_rate = (
    (df_filtered["Escalation Needed"] == "Yes").mean()
    if not df_filtered.empty
    else 0.0
)
auto_resolved_rate = 1 - escalation_rate if not df_filtered.empty else 0.0

with kpi1:
    st.metric("New tickets in range", new_in_range)
with kpi2:
    st.metric("Auto‑resolution rate", f"{auto_resolved_rate*100:.0f}%")
with kpi3:
    st.metric("Escalation rate", f"{escalation_rate*100:.0f}%")

# 5. Charts
st.subheader("Visual Analytics")
# 让左边更宽、右边略窄
left, right = st.columns([3, 2])

# Sentiment bar chart
with left:
    st.markdown("**Sentiment distribution over time**")
    if not df_filtered.empty:
        sentiment_data = (
            df_filtered.groupby(["Created Date", "Sentiment"])
            .size()
            .reset_index(name="count")
        )

        # 根据天数调节柱宽，<=7 天时更粗，更多时自动变细
        n_days = sentiment_data["Created Date"].nunique()
        bar_width = 40 if n_days <= 7 else 20

        chart1 = (
            alt.Chart(sentiment_data)
            .mark_bar(size=bar_width)
            .encode(
                x=alt.X(
                    "Created Date:T",
                    title="Date",
                    axis=alt.Axis(labelColor="#4a4a4a", titleColor="#4a4a4a"),
                ),
                y=alt.Y(
                    "count:Q",
                    title="Ticket count",
                    axis=alt.Axis(labelColor="#4a4a4a", titleColor="#4a4a4a"),
                ),
                color=alt.Color(
                    "Sentiment:N",
                    scale=alt.Scale(
                        domain=["Negative", "Non-Negative"],
                        range=["#ff6b6b", "#4dabf7"],
                    ),
                    legend=alt.Legend(
                        orient="bottom",
                        title="Sentiment",
                        labelColor="#4a4a4a",
                        titleColor="#4a4a4a",
                    ),
                ),
            )
            .properties(height=300)
            .configure_axis(gridColor="#e3e6f0")
        )
        st.altair_chart(chart1, use_container_width=True)
    else:
        st.info("No tickets in the selected date range.")

# Ticket type pie chart
with right:
    st.markdown("**Ticket type distribution**")
    if not df_filtered.empty:
        type_data = (
            df_filtered.groupby("Type")
            .size()
            .reset_index(name="count")
        )

        chart2 = (
            alt.Chart(type_data)
            .mark_arc()
            .encode(
                theta=alt.Theta("count:Q", title="Tickets"),
                color=alt.Color(
                    "Type:N",
                    legend=alt.Legend(
                        orient="bottom",
                        title="Type",
                        columns=2,      # one row 2 items
                        labelLimit=200, # avoid text truncation
                        labelColor="#4a4a4a",
                        titleColor="#4a4a4a",
                    ),
                ),
                tooltip=["Type", "count"],
            )
            .properties(height=300)
        )
        st.altair_chart(chart2, use_container_width=True)
    else:
        st.info("No tickets in the selected date range.")
