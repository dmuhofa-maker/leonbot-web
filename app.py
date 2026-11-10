import os
import streamlit as st
from dotenv import load_dotenv
from groq import Groq

# Load your GROQ_API_KEY
load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

# Configure the browser tab title and layout
st.set_page_config(page_title="LeonBot AI", page_icon="🤖", layout="centered")

SYSTEM_PROMPT = {
    "role": "system",
    "content": (
        "You are LeonBot, a friendly, street-smart tech assistant created by Lennon. "
        "Always speak simply, keep answers clear and smooth, and greet every user warmly. "
        "If anyone asks who created or built you, proudly introduce Lennon as your creator."
    )
}

# Left sidebar
with st.sidebar:
    st.title("🤖 LeonBot AI")
    st.caption("Created by Lennon")
    if st.button("➕ New Chat", use_container_width=True):
        st.session_state.messages = [SYSTEM_PROMPT]
        st.rerun()

st.title("What can I help you with?")
st.caption("LeonBot AI — Your free, fast AI assistant created by Lennon.")

# Initialize conversation memory
if "messages" not in st.session_state:
    st.session_state.messages = [SYSTEM_PROMPT]

# Display all past chat bubbles
for msg in st.session_state.messages:
    if msg["role"] != "system":
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

# ChatGPT-style input box at the bottom of the screen
if prompt := st.chat_input("Message LeonBot..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            try:
                response = client.chat.completions.create(
                    model="openai/gpt-oss-120b",
                    messages=st.session_state.messages  # type: ignore
                )
                reply = response.choices.message.content
                st.markdown(reply)
                st.session_state.messages.append({"role": "assistant", "content": reply})
            except Exception as e:
                st.error(f"Error: {e}")
