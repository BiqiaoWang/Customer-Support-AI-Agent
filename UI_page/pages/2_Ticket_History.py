import streamlit as st
import pandas as pd
import datetime as dt

st.set_page_config(layout="wide")
st.title("Ticket History")

# 1) Check tickets
if "tickets" not in st.session_state or st.session_state.tickets is None or st.session_state.tickets.empty:
    st.warning("No tickets yet. Please create one in the Workspace page.")
    st.stop()

df = st.session_state.tickets.copy()
df["Created Date"] = pd.to_datetime(df["Created Time"], format="%m-%d-%Y", errors="coerce").dt.date

# 2) Filters
st.subheader("Filters")
c1, c2 = st.columns(2)
with c1:
    start_date = st.date_input(
        "From",
        value=df["Created Date"].min() if not df.empty else dt.date.today(),
        key="hist_from",
    )
with c2:
    end_date = st.date_input(
        "To",
        value=df["Created Date"].max() if not df.empty else dt.date.today(),
        key="hist_to",
    )

df_filtered = df[(df["Created Date"] >= start_date) & (df["Created Date"] <= end_date)].copy()
df_sorted = df_filtered.sort_values(by=["Created Date", "ID"], ascending=[False, False])

# 3) Table
st.subheader("History Tickets")
cols_to_show = ["ID", "Created Time", "Status", "Type", "Sentiment", "Escalation Needed"]
table_data = df_sorted[cols_to_show] if not df_sorted.empty else df_sorted

st.dataframe(
    table_data,
    use_container_width=True,
    height=520,
)
