"""
Streamlit UI for the FDA Drug Labels Chatbot.

This file talks to the FastAPI backend via HTTP.
Backend: http://localhost:8000/chat
"""
import uuid
import requests
import streamlit as st
import os

# BACKEND_URL = "http://localhost:8000/chat"
# REQUEST_TIMEOUT = 60  # seconds
BACKEND_URL = os.getenv(
    "BACKEND_URL",
    "http://localhost:8000/chat"
)
REQUEST_TIMEOUT = 60

# ─── Page setup ───────────────────────────────────────────────────────
st.set_page_config(
    page_title="FDA Drug Labels Chatbot",
    page_icon="💊",
    layout="centered",
)


# ─── Session state initialization ─────────────────────────────────────
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())

if "messages" not in st.session_state:
    st.session_state.messages = []


# ─── Backend call helper ──────────────────────────────────────────────
def ask_backend(question: str, session_id: str) -> str:
    """
    Send a question to the FastAPI backend and return the answer.
    Returns an error message on failure.
    """
    try:
        response = requests.post(
            BACKEND_URL,
            json={"question": question, "session_id": session_id},
            timeout=REQUEST_TIMEOUT,
        )
        response.raise_for_status()
        data = response.json()
        return data.get("answer", "No answer received.")
    except requests.exceptions.ConnectionError:
        return "❌ Error: Could not connect to the backend. Is the FastAPI server running?"
    except requests.exceptions.Timeout:
        return "❌ Error: The backend took too long to respond. Please try again."
    except requests.exceptions.HTTPError as e:
        return f"❌ Error: Backend returned HTTP {e.response.status_code}."
    except Exception as e:
        return f"❌ Unexpected error: {e}"


# ─── Header ───────────────────────────────────────────────────────────
st.title("💊 FDA Drug Labels Chatbot")
st.caption(
    "Ask about FDA-approved monoclonal antibody drugs. "
    "Answers are based only on the labels in the database."
)


# ─── Debug info (collapsible) ─────────────────────────────────────────
with st.expander("🔧 Session info (debug)"):
    st.write(f"**Session ID:** `{st.session_state.session_id}`")
    st.write(f"**Messages in history:** {len(st.session_state.messages)}")


# ─── Display chat history ─────────────────────────────────────────────
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])


# ─── Chat input ───────────────────────────────────────────────────────
user_input = st.chat_input("Ask a question about the drugs...")

if user_input:
    # 1. Add user message to history and display it
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    # 2. Call the backend
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            answer = ask_backend(user_input, st.session_state.session_id)
        st.markdown(answer)

    # 3. Add assistant message to history
    st.session_state.messages.append({"role": "assistant", "content": answer})