import streamlit as st

from src.main_logic_rag import app, GREETING


st.set_page_config(page_title="AI Support Assistant", page_icon="🤖")
st.title("AI Support Assistant")

if "state" not in st.session_state:
    # Pre-seed greeting in history so graph's greet node will skip.
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

# Render history so far (initial greeting included)
for msg in st.session_state.state.get("history", []):
    role = msg.get("role", "assistant")
    content = msg.get("content", "")
    with st.chat_message("assistant" if role == "assistant" else "user"):
        st.markdown(content)

# If ticket is closed or escalated, block further input.
status_flag = (st.session_state.state.get("status") or "").upper()
if status_flag in {"CLOSED", "ESCALATED"}:
    msg = "This ticket is closed." if status_flag == "CLOSED" else "This ticket has been escalated to a human agent."
    st.info(msg)
    with st.expander("State (debug)"):
        st.json(st.session_state.state)
    st.stop()

pending = st.session_state.state.get("pending_question") or ""
response_text = st.session_state.state.get("response") or ""
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
    # Disable free text while waiting for button choice
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
    # Carry over prior state, override query and flags for this turn.
    base_state = {k: v for k, v in st.session_state.state.items() if k != "query"}
    base_state.update(
        {
            "query": prompt_value,
            "resolved": False,
            "wants_human": False,
        }
    )
    try:
        # Show user input immediately
        with st.chat_message("user"):
            st.markdown(prompt_value)
        # Transient waiting message
        wait_placeholder = st.empty()
        with wait_placeholder.chat_message("assistant"):
            st.markdown("Please wait a moment, thank you for your patience.")
        result = app.invoke(base_state)
        st.session_state.state = result
        st.rerun()
    except Exception as exc:
        st.error(f"Error: {exc}")
        st.stop()

# Debug/inspect section (optional)
with st.expander("State (debug)"):
    st.json(st.session_state.state)
