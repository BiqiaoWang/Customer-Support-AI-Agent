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


# 4. KPIs
st.subheader("Support Ticket Analytics")
kpi1, kpi2, kpi3 = st.columns(3)

total_tickets = len(df_filtered)

escalation_rate = (
    (df_filtered["Escalation Needed"] == "Yes").mean()
    if not df_filtered.empty
    else 0.0
)
auto_resolved_rate = 1 - escalation_rate if not df_filtered.empty else 0.0

with kpi1:
    st.metric(
        f"Tickets ({start_date:%m-%d}→{end_date:%m-%d})",
        total_tickets
    )
with kpi2:
    st.metric(
        f"Auto‑resolution rate ({start_date:%m-%d}→{end_date:%m-%d})",
        f"{auto_resolved_rate*100:.0f}%"
    )
with kpi3:
    st.metric(
        f"Escalation rate ({start_date:%m-%d}→{end_date:%m-%d})",
        f"{escalation_rate*100:.0f}%"
    )




# 5. Charts
st.subheader("Visual Analytics")
# 让左边更宽、右边略窄
left, right = st.columns([3, 2])

# Sentiment bar chart
with left:
    st.markdown("**Sentiment distribution over time**")
    if not df_filtered.empty:
        # 1) 先按天 + 情绪聚合
        sentiment_data = (
            df_filtered.groupby(["Created Date", "Sentiment"])
            .size()
            .reset_index(name="count")
        )

        # 2) 构造最近 7 天完整日期序列（以当前过滤范围内的最大日期为结束）
        last_day = df_filtered["Created Date"].max()
        full_dates = pd.date_range(end=last_day, periods=7, freq="D").date
        full_df = pd.DataFrame({"Created Date": full_dates})

        # 3) 把聚合结果 merge 到完整日期上；没有数据的日期 count 为 0
        sentiment_full = full_df.merge(
            sentiment_data,
            on="Created Date",
            how="left",
        )
        sentiment_full["count"] = sentiment_full["count"].fillna(0)

        # 没有情绪标签的行，你可以默认成 "Non-Negative" 或 "No data"
        sentiment_full["Sentiment"] = sentiment_full["Sentiment"].fillna(
            "Non-Negative"
        )

        # 4) 排序 + 文本标签
        sentiment_full = sentiment_full.sort_values("Created Date")
        sentiment_full["Created Date Str"] = sentiment_full["Created Date"].apply(
            lambda d: d.strftime("%m-%d")
        )

        # 5) 根据天数调节柱宽（这里基本就是 7 天）
        n_days = sentiment_full["Created Date"].nunique()
        bar_width = 40 if n_days <= 7 else 20

        tick_values = pd.to_datetime(full_dates)

        chart1 = (
            alt.Chart(sentiment_full)
            .mark_bar(size=bar_width)
            .encode(
                x=alt.X(
                    "Created Date:T",
                    title="Date (last 7 days)",
                    axis=alt.Axis(format="%m-%d", values=tick_values, labelColor="#4a4a4a", titleColor="#4a4a4a"),
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
                tooltip=[
                  alt.Tooltip("Created Date:T", title="Date", format="%m-%d"),
                  alt.Tooltip("Sentiment:N"),
                  alt.Tooltip("count:Q"),
                ],
            )
            .properties(height=300)
            .configure_axis(gridColor="#e3e6f0")
        )
        st.altair_chart(chart1, use_container_width=True)
    else:
        st.info("No tickets in the selected date range.")

# Ticket type pie chart（保持不变）
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
                        columns=2,
                        labelLimit=200,
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
