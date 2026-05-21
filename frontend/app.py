# frontend/app.py
import requests
import streamlit as st
import os
import re

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

# 5. Sidebar Setup (Voice Command Integrated Successfully)
with st.sidebar:
    st.markdown("<h3 style='color: #00FFA3;'>System Status</h3>", unsafe_allow_html=True)
    st.success("Connected to Render Cloud")
    
    st.markdown("---")
    
    # Clear Chat Actions
    st.markdown("<h4 style='color: #94A3B8;'>Chat Actions</h4>", unsafe_allow_html=True)
    if st.button("🗑️ Clear Chat History", use_container_width=True):
        st.session_state.messages = [
            {"role": "assistant", "content": "Hello! Chat history clear ho gayi hai. Mujhe batayein aapko Google Drive mein kya dhoondhna hai?"}
        ]
        st.rerun()

    # 🆕 VOICE COMMAND SEARCH WIDGET ADDED HERE
    st.markdown("---")
    st.markdown("<h4 style='color: #00FFA3;'>🎙️ Voice Command Search</h4>", unsafe_allow_html=True)
    st.write("Click 'Start Recording', speak your file name, then click 'Stop'.")
    
    from streamlit_mic_recorder import mic_recorder
    
    audio_data = mic_recorder(
        start_prompt="🎵 Start Recording",
        stop_prompt="🛑 Stop & Search",
        just_once=True,
        key='voice_search_mic'
    )
    # Agar user ne voice record karli hai aur audio data mil gaya hai
    if audio_data and audio_data.get('bytes'):
        st.info("🎙️ Voice captured! Processing speech-to-text...")

        # 🧪 Local testing verification audio track layout (optional)
        # st.audio(audio_data['bytes']) 

        # Note: Agle phase mein is raw audio_data['bytes'] ko hum speech-to-text API 
        # (jaise OpenAI Whisper ya Gemini Audio Transcription) ke short URL par process karenge.
        # Abhi ke liye hum model ko simulate karne ke liye placeholder text update kar rahe hain:
        st.warning("Speech-to-text API module initializing. Integrate your API keys to run live transcriptions!")

    st.markdown("---")
    st.markdown("<h4 style='color: #94A3B8;'>How to use:</h4>", unsafe_allow_html=True)
    st.write("1. Share your Drive folder with the Service Account email.")
    st.write("2. Type natural questions like *'Find my project sheet'*.")

# 6. Initialize Chat History
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "Hello! Please tell me what file you are looking for in your Google Drive."}
    ]

# 7. Display Past Messages on Screen (Updated for HTML Cards & Preview support)
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        if message.get("is_html"):
            st.markdown(message["content"], unsafe_allow_html=True)
        else:
            st.markdown(message["content"])
        
        # Past session memory mein bhi expander/preview load ho sake
        if message.get("embed_url") and message.get("file_name"):
            with st.expander(f"👁️ Quick Preview: {message['file_name']}"):
                st.components.v1.iframe(message["embed_url"], height=500, scrolling=True)

# 8. User Input and Response Processing Logic
if user_input := st.chat_input("Search your Google Drive..."):
    # Display user message instantly
    with st.chat_message("user"):
        st.markdown(user_input)
    st.session_state.messages.append({"role": "user", "content": user_input})

    # Show a premium custom pulsing loader instead of a boring spinner
    with st.chat_message("assistant"):
        loader_placeholder = st.empty()
        loader_placeholder.markdown('<div class="ai-pulse-loader">🤖 Agent is scanning your Google Drive cloud space...</div>', unsafe_allow_html=True)
        
        try:
            # Sending request to backend
            response = requests.post(f"{BACKEND_URL}/chat", json={"message": user_input}, timeout=60)
            loader_placeholder.empty() # Remove loader once data arrives
            
            if response.status_code == 200:
                ai_response = response.json().get("response", "No response text found.")
                
                # 🔍 Regex to find Google Drive Links from Gemini's response
                markdown_link_pattern = r'\[([^\]]+)\]\((https:\/\/drive\.google\.com\/[^)]+)\)'
                raw_url_pattern = r'(https:\/\/drive\.google\.com\/file\/d\/[^\s\)]+)'
                
                md_links = re.findall(markdown_link_pattern, ai_response)
                
                if md_links:
                    clean_text = re.sub(markdown_link_pattern, '', ai_response).strip()
                    if clean_text and not clean_text.startswith("Found"):
                        st.markdown(clean_text)
                        st.session_state.messages.append({"role": "assistant", "content": clean_text})
                    
                    # Saari files ke liye alag-alag card aur preview window banayein
                    for file_name, file_url in md_links:
                        card_html = f"""
                        <div class="file-card">
                            <div>
                                <span style='color: #94A3B8; font-size: 0.85rem; display:block;'>GOOGLE DRIVE FILE</span>
                                <strong style='font-size: 1.05rem; color: #F8FAFC;'>📄 {file_name.strip()}</strong>
                            </div>
                            <div>
                                <a href="{file_url.strip()}" target="_blank" class="file-link">🗂️ Open File</a>
                            </div>
                        </div>
                        """
                        st.markdown(card_html, unsafe_allow_html=True)
                        
                        # Preview Configuration
                        file_id_match = re.search(r'/d/([^/]+)', file_url)
                        embed_url = None
                        if file_id_match:
                            file_id = file_id_match.group(1)
                            embed_url = f"https://drive.google.com/file/d/{file_id}/preview"
                            with st.expander(f"👁️ Quick Preview: {file_name.strip()}"):
                                st.components.v1.iframe(embed_url, height=500, scrolling=True)
                        
                        # History State Append
                        st.session_state.messages.append({
                            "role": "assistant", 
                            "content": card_html, 
                            "is_html": True,
                            "embed_url": embed_url,
                            "file_name": file_name.strip()
                        })
                        
                elif re.search(raw_url_pattern, ai_response):
                    urls = re.findall(raw_url_pattern, ai_response)
                    st.markdown(ai_response)
                    st.session_state.messages.append({"role": "assistant", "content": ai_response})
                    
                    for url in urls:
                        card_html = f"""
                        <div class="file-card">
                            <div>
                                <span style='color: #94A3B8; font-size: 0.85rem; display:block;'>GOOGLE DRIVE FILE</span>
                                <strong style='font-size: 1.05rem; color: #F8FAFC;'>📄 Click to view document</strong>
                            </div>
                            <div>
                                <a href="{url.strip()}" target="_blank" class="file-link">🗂️ Open File</a>
                            </div>
                        </div>
                        """
                        st.markdown(card_html, unsafe_allow_html=True)
                        
                        file_id_match = re.search(r'/d/([^/]+)', url)
                        embed_url = None
                        if file_id_match:
                            file_id = file_id_match.group(1)
                            embed_url = f"https://drive.google.com/file/d/{file_id}/preview"
                            with st.expander("👁️ Quick Preview: View Document"):
                                st.components.v1.iframe(embed_url, height=500, scrolling=True)
                                
                        st.session_state.messages.append({
                            "role": "assistant", 
                            "content": card_html, 
                            "is_html": True,
                            "embed_url": embed_url,
                            "file_name": "View Document"
                        })
                else:
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

# 🛑 Iske niche koi extra text (jaise 'add karo') nahi hona chahiye!