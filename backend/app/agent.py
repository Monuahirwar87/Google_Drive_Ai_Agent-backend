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
@tool
def google_drive_search(keyword: str):
    """
    Search Google Drive for files related to the given keyword.
    """
    return search_drive(keyword)


# Initialize Gemini model
llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    temperature=0,
)

# Register tools
tools = [google_drive_search]

# Create LangGraph ReAct agent
agent = create_react_agent(
    model=llm,
    tools=tools,
)