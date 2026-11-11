import os
import json
from datetime import datetime
import streamlit as st
from dotenv import load_dotenv
from groq import Groq
from pypdf import PdfReader
from ddgs import DDGS

# Load your GROQ_API_KEY
load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

# Configure the browser tab title and layout
st.set_page_config(page_title="LeonBot AI", page_icon="🤖", layout="centered")

def get_system_prompt(notes_text=""):
    today = datetime.now().strftime("%B %d, %Y")
    base_prompt = (
        f"You are LeonBot, a friendly, street-smart tech assistant and Study Tutor created by Lennon. Today's date is {today}. "
        "Always speak simply, keep answers clear and smooth, and greet every user warmly. "
        "If anyone asks who created or built you, proudly introduce Lennon as your creator. "
        "You have access to a `search_web` tool. Use it automatically whenever a user asks about current news, "
        "live sports scores, recent events, weather, prices, or facts you are unsure about."
    )
    if notes_text:
        base_prompt += (
            "\n\nThe user has uploaded the following study notes. Use these notes to help them study, "
            "explain difficult topics simply, and quiz them when asked:\n\n"
            f"--- STUDY NOTES ---\n{notes_text[:12000]}\n--- END OF NOTES ---"
        )
    return {"role": "system", "content": base_prompt}

SEARCH_TOOL = [
    {
        "type": "function",
        "function": {
            "name": "search_web",
            "description": "Search the live internet for up-to-date news, sports scores, current events, and facts.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The search query to look up on the internet."
                    }
                },
                "required": ["query"]
            }
        }
    }
]

def search_web(query):
    results = DDGS().text(query, max_results=5)
    if not results:
        return "No search results found."
    formatted = []
    for r in results:
        formatted.append(f"Title: {r['title']}\nSummary: {r['body']}\nSource: {r['href']}")
    return "\n\n".join(formatted)

def extract_text_from_file(uploaded_file):
    if uploaded_file.name.lower().endswith(".pdf"):
        reader = PdfReader(uploaded_file)
        pages = [page.extract_text() or "" for page in reader.pages]
        return "\n".join(pages)
    else:
        return uploaded_file.read().decode("utf-8", errors="ignore")

# Initialize session variables
if "notes_text" not in st.session_state:
    st.session_state.notes_text = ""
if "messages" not in st.session_state:
    st.session_state.messages = [get_system_prompt()]

# Left sidebar
with st.sidebar:
    st.title("🤖 LeonBot AI")
    st.caption("Created by Lennon")

    if st.button("➕ New Chat", use_container_width=True):
        st.session_state.messages = [get_system_prompt(st.session_state.notes_text)]
        st.rerun()

    st.divider()
    st.subheader("📚 Study Tutor")
    uploaded_file = st.file_uploader("Upload study notes (PDF or TXT)", type=["pdf", "txt"])

    if uploaded_file is not None:
        extracted = extract_text_from_file(uploaded_file)
        if extracted != st.session_state.notes_text:
            st.session_state.notes_text = extracted
            st.session_state.messages = [get_system_prompt(extracted)]
            st.success(f"Loaded: {uploaded_file.name}")

    quiz_clicked = False
    if st.session_state.notes_text:
        if st.button("📝 Quiz Me on My Notes", use_container_width=True):
            quiz_clicked = True

st.title("What can I help you with?")
st.caption("LeonBot AI — Your free AI assistant, Study Tutor & live web search tool created by Lennon.")

# Display all past chat bubbles
for msg in st.session_state.messages:
    if isinstance(msg, dict) and msg.get("role") in ("user", "assistant") and msg.get("content"):
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

# Handle either typed message OR Quiz button click
user_prompt = st.chat_input("Message LeonBot, ask live news, or ask about your notes...")
if quiz_clicked:
    user_prompt = "Create a short 3-question multiple-choice quiz based on my uploaded study notes. Wait for my answers before showing the solutions!"

if user_prompt:
    st.session_state.messages.append({"role": "user", "content": user_prompt})
    with st.chat_message("user"):
        st.markdown(user_prompt)

    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            try:
                response = client.chat.completions.create(
                    model="openai/gpt-oss-120b",
                    messages=st.session_state.messages,  # type: ignore
                    tools=SEARCH_TOOL,  # type: ignore
                    tool_choice="auto"
                )
                response_message = response.choices[0].message

                # Check if LeonBot decided to search the live internet
                if response_message.tool_calls:
                    st.session_state.messages.append(response_message)

                    for tool_call in response_message.tool_calls:
                        args = json.loads(tool_call.function.arguments)
                        query = args.get("query", user_prompt)
                        with st.spinner(f"🔍 Searching the web for: {query}..."):
                            web_data = search_web(query)

                        st.session_state.messages.append({
                            "role": "tool",
                            "tool_call_id": tool_call.id,
                            "name": "search_web",
                            "content": web_data
                        })

                    final_response = client.chat.completions.create(
                        model="openai/gpt-oss-120b",
                        messages=st.session_state.messages  # type: ignore
                    )
                   reply = final_response.choices[0].message.content
                else:
                    reply = response_message.content

                st.markdown(reply)
                st.session_state.messages.append({"role": "assistant", "content": reply})
            except Exception as e:
                st.error(f"Error: {e}")
