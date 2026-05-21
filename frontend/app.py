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

# 3. Backend Base URL Config (Bina trailing slash ya /chat ke)
BACKEND_URL = os.getenv("BACKEND_URL", "https://google-drive-ai-agent-backend.onrender.com")

# 4. Header Section UI
st.markdown("<h1>🤖 Google Drive AI Agent</h1>", unsafe_allow_html=True)
st.markdown("<p style='color: #94A3B8; font-size: 1.1rem;'>Ask questions or search files securely inside your Google Drive folder.</p>", unsafe_allow_html=True)
st.markdown("---")

# 5. Sidebar Setup (Updated with Clear Chat Button)
with st.sidebar:
    st.markdown("<h3 style='color: #00FFA3;'>System Status</h3>", unsafe_allow_html=True)
    st.success("Connected to Render Cloud")
    
    st.markdown("---")
    
    # 🆕 Clear Chat Actions
    st.markdown("<h4 style='color: #94A3B8;'>Chat Actions</h4>", unsafe_allow_html=True)
    if st.button("🗑️ Clear Chat History", use_container_width=True):
        st.session_state.messages = [
            {"role": "assistant", "content": "Hello! Chat history clear ho gayi hai. Mujhe batayein aapko Google Drive mein kya dhoondhna hai?"}
        ]
        st.rerun()

    st.markdown("---")
    st.markdown("<h4 style='color: #94A3B8;'>How to use:</h4>", unsafe_allow_html=True)
    st.write("1. Share your Drive folder with the Service Account email.")
    st.write("2. Type natural questions like *'Find my project sheet'*.")

# 6. Initialize Chat History
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "Hello! Please tell me what file you are looking for in your Google Drive."}
    ]

# 7. Display Past Messages on Screen (Updated for HTML Cards support)
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        # Agar message ek HTML card hai toh unsafe_allow_html use karein, nahi toh normal text
        if message.get("is_html"):
            st.markdown(message["content"], unsafe_allow_html=True)
        else:
            st.markdown(message["content"])

# 8. User Input and Response Processing Logic
if user_input := st.chat_input("Search your Google Drive..."):
    # Display user message instantly
    with st.chat_message("user"):
        st.markdown(user_input)
    st.session_state.messages.append({"role": "user", "content": user_input})

    # Show a premium custom pulsing loader instead of a boring spinner
    with st.chat_message("assistant"):
        loader_placeholder = st.empty()
        # Custom HTML pulsing text loader
        loader_placeholder.markdown('<div class="ai-pulse-loader">🤖 Agent is scanning your Google Drive cloud space...</div>', unsafe_allow_html=True)
        
        try:
            # Sending request to backend
            response = requests.post(f"{BACKEND_URL}/chat", json={"message": user_input}, timeout=60)
            loader_placeholder.empty() # Remove loader once data arrives
            
            if response.status_code == 200:
                ai_response = response.json().get("response", "No response text found.")
                
                # 🆕 Visual Cards Logic: Check if the response looks like a file path or link
                # Agar backend response mein 'http' ya 'drive.google.com' jaisa link aata hai
                if "http" in ai_response and "drive.google.com" in ai_response:
                    # Hum link aur text ko clean karke premium HTML card mein wrap kar rahe hain
                    file_name = ai_response.split("http")[0].replace("Found file:", "").strip()
                    file_url = "http" + ai_response.split("http")[1].strip()
                    
                    card_html = f"""
                    <div class="file-card">
                        <div>
                            <span style='color: #94A3B8; font-size: 0.85rem; display:block;'>GOOGLE DRIVE FILE</span>
                            <strong style='font-size: 1.1rem; color: #F8FAFC;'>📄 {file_name if file_name else "Requested Document"}</strong>
                        </div>
                        <div>
                            <a href="{file_url}" target="_blank" class="file-link">🗂️ Open File</a>
                        </div>
                    </div>
                    """
                    st.markdown(card_html, unsafe_allow_html=True)
                    st.session_state.messages.append({"role": "assistant", "content": card_html, "is_html": True})
                else:
                    # Normal conversational response text
                    st.markdown(ai_response)
                    st.session_state.messages.append({"role": "assistant", "content": ai_response})
                    
            else:
                ai_response = f"⚠️ Backend Server Error: Code {response.status_code}"
                st.markdown(ai_response)
                st.session_state.messages.append({"role": "assistant", "content": ai_response})
                
        except requests.exceptions.RequestException as e:
            loader_placeholder.empty()
            ai_response = "❌ Connection Error: Backend server is not responding."
            st.markdown(ai_response)
            st.session_state.messages.append({"role": "assistant", "content": ai_response})