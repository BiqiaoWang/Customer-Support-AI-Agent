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
        status_value = str(row.get("Status", "")).upper()
        is_escalated = status_value == "ESCALATED"
        if is_escalated:
            state_data = (details or {}).get("state", {})
            ragcards = state_data.get("ragcards") or []
            summary = (state_data.get("ticket_summary") or "").strip()
            categories = state_data.get("escalation_categories") or []
            priority = [
                "user_confirmed_escalation",
                "user_requested_human",
                "negative_sentiment",
                "billing_high_risk",
                "sales_presales_sensitive",
                "security_sensitive",
                "low_confidence_ticket_type",
                "unknown",
            ]
            reason = ""
            for item in priority:
                if item in categories:
                    reason = item
                    break
            if not reason and categories:
                reason = categories[0]
            if not reason:
                reason = "unknown"
            cards_text = ", ".join(ragcards) if ragcards else "None"
            summary_text = summary or "Not available."
            st.markdown("**Escalation details**")
            st.write("RAG Cards:", cards_text)
            st.write("Ticket Summary:", summary_text)
            st.write("Escalation Reason:", reason)
