import streamlit as st
import pandas as pd

st.title("Ticket Detail")

# 1. Check tickets
if "tickets" not in st.session_state or st.session_state.tickets.empty:
    st.warning("No tickets yet. Please create one in the Workspace page.")
    st.stop()

df = st.session_state.tickets

# 2. Select ticket ID
ticket_id = st.selectbox("Select ticket ID", options=df["ID"].tolist())

ticket_row = df[df["ID"] == ticket_id]

if ticket_row.empty:
    st.error("Ticket not found.")
    st.stop()

row = ticket_row.iloc[0]

# --- Divider + English summary title ---
st.markdown("---")
st.subheader("Ticket summary")

# 明细表（保留）
st.dataframe(ticket_row, use_container_width=True)

# 4. Conversation / event history
st.subheader("Conversation & events")
left, right = st.columns([3, 2])

details_store = st.session_state.get("ticket_details", {})
details = details_store.get(ticket_id)

if not details:
    with left:
        st.info("No conversation history has been saved for this ticket yet.")
else:
    history = details.get("history", [])
    events = details.get("events", [])

    # Left: conversation bubbles
    with left:
        st.markdown("**Conversation history**")
        for msg in history:
            role = msg.get("role", "assistant")
            content = msg.get("content", "")
            bubble_bg = "#f5f6fa" if role == "assistant" else "#e8f4ff"
            align = "flex-start" if role == "assistant" else "flex-end"

            st.markdown(
                f"""
                <div style="display:flex; justify-content:{align};">
                  <div style="
                    max-width:80%;
                    background:{bubble_bg};
                    padding:10px 14px;
                    border-radius:12px;
                    margin:4px 0;
                    font-size:14px;
                  ">
                    {content}
                  </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        st.markdown("**Event log**")
        for e in events:
            st.write(f"- {e}")

    # Right: reserved area
    with right:
        st.markdown("**Ticket notes**")
        st.info("Reserved for Owner / Tags / SLA / internal notes.")
