import requests
import streamlit as st
import os

BACKEND_URL = os.getenv("BACKEND_URL", "https://google-drive-ai-agent-backend.onrender.com")
print(BACKEND_URL)

# Page configuration
st.set_page_config(
    page_title="Google Drive Search Agent",
    page_icon="📁",
)

st.title("📁 Google Drive Search Agent")
st.write("Ask questions about the files in your Google Drive.")

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display previous messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Chat input
user_input = st.chat_input("Search your Google Drive...")

if user_input:
    # Show user message
    st.session_state.messages.append(
        {"role": "user", "content": user_input}
    )

    with st.chat_message("user"):
        st.markdown(user_input)

    # Send request to FastAPI backend
    with st.chat_message("assistant"):
        with st.spinner("Searching Google Drive..."):
            response = requests.post(
                f"{BACKEND_URL}/chat",
                json={"message": user_input},
                timeout=60,
            )

            if response.status_code == 200:
                answer = response.json()["response"]
            else:
                answer = f"Error: {response.status_code}"

            st.markdown(answer)

    # Save assistant response
    st.session_state.messages.append(
        {"role": "assistant", "content": answer}
    )