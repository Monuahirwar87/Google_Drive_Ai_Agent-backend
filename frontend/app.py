# frontend/app.py
import requests
import streamlit as st
import os

# 1. Page Configuration (Must be at the very top of the script)
st.set_page_config(
    page_title="Drive AI Agent",
    page_icon="🤖",
    layout="centered"
)

# 2. Load Custom CSS
css_path = os.path.join(os.path.dirname(__file__), "static", "style.css")
if os.path.exists(css_path):
    with open(css_path) as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# 3. Backend URL Config (Your Live Render Server URL)
BACKEND_URL = os.getenv("BACKEND_URL", "https://google-drive-ai-agent-backend.onrender.com")

# 4. Header Section UI
st.markdown("<h1>🤖 Google Drive AI Agent</h1>", unsafe_allow_html=True)
st.markdown("<p style='color: #94A3B8; font-size: 1.1rem;'>Ask questions or search files securely inside your Google Drive folder.</p>", unsafe_allow_html=True)
st.markdown("---")

# 5. Sidebar Setup (For Information & Controls)
with st.sidebar:
    st.markdown("<h3 style='color: #00FFA3;'>System Status</h3>", unsafe_allow_html=True)
    st.success("Connected to Render Cloud")
    
    st.markdown("---")
    st.markdown("<h4 style='color: #94A3B8;'>How to use:</h4>", unsafe_allow_html=True)
    st.write("1. Share your Drive folder with the Service Account email.")
    st.write("2. Type natural questions like *'Find my project sheet'*.")

# 6. Initialize Chat History
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "Hello! Please tell me what file you are looking for in your Google Drive."}
    ]

# 7. Display Past Messages on Screen
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# 8. User Input and Response Processing Logic
if user_input := st.chat_input("Search your Google Drive..."):
    # Display user message instantly
    with st.chat_message("user"):
        st.markdown(user_input)
    st.session_state.messages.append({"role": "user", "content": user_input})

    # Show a loading spinner while waiting for the API response
    with st.chat_message("assistant"):
        with st.spinner("Searching files in Google Drive..."):
            try:
                # Sending request to the live Render backend URL
                response = requests.post(BACKEND_URL, json={"engine": user_input}, timeout=30)
                
                if response.status_code == 200:
                    ai_response = response.json().get("response", "No response text found.")
                else:
                    ai_response = f"⚠️ Backend Server Error: Code {response.status_code}"
            except requests.exceptions.RequestException as e:
                ai_response = "❌ Connection Error: The backend server is not responding. Please check if your Render service is active."

            st.markdown(ai_response)
            st.session_state.messages.append({"role": "assistant", "content": ai_response})