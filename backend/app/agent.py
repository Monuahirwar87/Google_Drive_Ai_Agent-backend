# backend/app/agent.py
from pathlib import Path

from dotenv import load_dotenv
from langchain.tools import tool
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.prebuilt import create_react_agent

from app.tools import search_drive

# Load environment variables from backend/.env
ENV_PATH = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(ENV_PATH)


# Convert our Python function into a LangChain tool
# Tool 1: File Search Tool
@tool
def google_drive_search(keyword: str):
    """
    Search Google Drive for files related to the given keyword.
    """
    return search_drive(keyword)

# 🆕 Tool 2: File Content Reader Tool (Naya Add Kiya)
@tool
def read_file_content(file_id: str):
    """
    Use this tool ONLY when the user explicitly asks to read, summarize, analyze, 
    extract info, or ask questions FROM INSIDE a specific file's content.
    Input MUST be a valid Google Drive File ID string.
    """
    return read_drive_file_content(file_id)


# Initialize Gemini model
llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    temperature=0,
)

# Register tools
tools = [google_drive_search]

# 🆕 YAHAN ADD KIYA HAI: System Instruction pure plaintext string mein
system_instruction = """You are an advanced Google Drive AI Agent. Your job is to help users find and manage documents from their connected cloud storage.

⚠️ CRITICAL INSTRUCTION FOR FILE LINKS:
When providing a list of files found in Google Drive, you MUST format each file as a markdown link using its exact name and webViewLink/alternateLink provided by the tool. 
Format should strictly be: [Exact_File_Name.pdf](https://drive.google.com/...) listed as bullet points. 

Do not output raw plain text for filenames. Every single file mentioned must have its corresponding link attached so the frontend can build dynamic visual cards.
"""

# Create LangGraph ReAct agent
# 🆕 Fixed: 'state_modifier' ko badal kar 'prompt' kiya taaki crash na ho
agent = create_react_agent(
    model=llm,
    tools=tools,
    prompt=system_instruction  
)