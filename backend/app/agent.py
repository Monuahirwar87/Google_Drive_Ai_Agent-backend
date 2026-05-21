# backend/app/agent.py
import os
from pathlib import Path
from dotenv import load_dotenv
from langchain.tools import tool
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.prebuilt import create_react_agent

# Backend tools functions import
from app.tools import search_drive, read_drive_file_content

# Load environment variables safely (Local testing fallback ke liye)
ENV_PATH = Path(__file__).resolve().parent.parent / ".env"
if ENV_PATH.exists():
    load_dotenv(ENV_PATH)

# Initialize Gemini 2.5 Flash model using environment key
api_key = os.getenv("GEMINI_API_KEY")
llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    google_api_key=api_key,
    temperature=0
)

# =====================================================================
# 🛠️ LANGCHAIN TOOLS WRAPPERS DEFINITION
# =====================================================================

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
tools = [google_drive_search, read_file_content]

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

# =====================================================================
# 🎯 LANGGRAPH REACT AGENT CREATION
# =====================================================================

# Using state_modifier string to append system instructions cleanly
agent = create_react_agent(
    model=llm,
    tools=tools,
    prompt=system_instruction  # Fixed prompt string config mapping
)