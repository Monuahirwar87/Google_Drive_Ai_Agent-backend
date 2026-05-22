# backend/app/agent.py
import os
from pathlib import Path
from dotenv import load_dotenv
from langchain.tools import tool
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.prebuilt import create_react_agent

# ✅ Safe conditional loading: Load .env ONLY during local development
if not os.getenv("RENDER"):  # Render automatically sets this variable
    ENV_PATH = Path(__file__).resolve().parent.parent / ".env"
    if ENV_PATH.exists():
        load_dotenv(ENV_PATH)

# =====================================================================
# 🎯 LAZY INITIALIZATION FUNCTION (Prevents Render Boot Crashes)
# =====================================================================
def get_agent_instance():
    """
    Dynamically initializes Gemini Model, tools, and LangGraph architecture 
    only when requested at runtime. This completely blocks Render boot validation crashes.
    """
    # Safe runtime import
    from app.tools import search_drive, read_drive_file_content

    # 1. Fetch Key and provide an absolute fallback string to satisfy Pydantic initialization phase
    gemini_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY") or "mock_key_override_to_pass_render_boot"

    # 2. Define LangChain Tools locally inside runtime execution context
    @tool
    def google_drive_search(keyword: str, folder_id: str = None):
        """
        Search Google Drive for files related to the given keyword.
        You can optionally pass a specific folder_id string to restrict the search.
        """
        # System injects folder scope automatically if available
        return search_drive(keyword, folder_id=folder_id)

    @tool
    def read_file_content(file_id: str):
        """
        Use this tool ONLY when the user explicitly asks to read, summarize, analyze, 
        extract info, or ask questions FROM INSIDE a specific file's content.
        Input MUST be a valid Google Drive File ID string.
        """
        return read_drive_file_content(file_id)

    # Register BOTH tools into the execution list
    tools_list = [google_drive_search, read_file_content]

    # 3. Initialize Model strictly inside function call context
    llm = ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",
        google_api_key=gemini_key,
        temperature=0,
        max_output_tokens=1000  # Token heavy usage control karne ke liye
    )

    # =====================================================================
    # 📝 HARDENED SYSTEM INSTRUCTIONS BLOCK (Combined Features)
    # =====================================================================
    system_instruction = """You are an advanced Google Drive AI Agent. Your job is to help users find, manage, and analyze documents from their connected cloud storage.

    ⚠️ CRITICAL INSTRUCTION FOR FILE LINKS (Feature 1 & 2):
    When providing a list of files found in Google Drive, you MUST format each file as a markdown link using its exact name and webViewLink/alternateLink provided by the tool. 
    Format should strictly be: [Exact_File_Name.pdf](https://drive.google.com/...) listed as bullet points. 

    Do not output raw plain text for filenames. Every single file mentioned must have its corresponding link attached so the frontend can build dynamic visual cards and iframe previews.

    📂 FOLDER SCOPE CONTEXT POLICY (Feature 4):
    You operate under a strict parent folder scope constraint environment.
    If a user query comes in, you must prioritize scanning within the provided session folder scope.
    """

    # 4. Return compiled ReAct Agent instance dynamically using prompt mapping
    return create_react_agent(
        model=llm,
        tools=tools_list,
        prompt=system_instruction
    )