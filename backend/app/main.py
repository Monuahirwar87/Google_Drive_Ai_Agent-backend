from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware  # 🆕 Import middleware
from pydantic import BaseModel
from app.agent import agent
from app.tools import get_all_folders  

# Create FastAPI application
app = FastAPI(title="Google Drive Search Agent")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://my-drive-ai-agent.streamlit.app"],  # Allow all origins (replace with specific domains in production)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request body schema
# 📂 Request Model ko update kiya folder_id field ke sath
class ChatRequest(BaseModel):
    message: str
    folder_id: str = None


# Response body schema
class ChatResponse(BaseModel):
    response: str


@app.get("/")
def root():
    return {"message": "Google Drive Search Agent is running!"}

# 🆕 NEW ENDPOINT: Frontend ke dropdown ko folders list dene ke liye
@app.get("/folders")
def list_folders():
    folders = get_all_folders()
    return {"folders": folders}

@app.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest):
    try:

        user_message = request.message
        
        # Agar specific folder select hai, toh system prompt ko control karne ke liye message mein inject karein
        if request.folder_id and request.folder_id != "all_drive":
            user_message += f" (Note: Strictly restrict your tool search parameters inside parent folder ID: {request.folder_id})"
        
        
        result = agent.invoke(
            {
                "messages": [
                    {
                        "role": "user",
                        "content": request.message,
                    }
                ]
            }
        )

        content = result["messages"][-1].content

        if isinstance(content, str):
            final_message = content
        elif isinstance(content, list):
            text_parts = []

            for item in content:
                if isinstance(item, dict) and item.get("type") == "text":
                    text_parts.append(item.get("text", ""))

            final_message = "\n".join(text_parts)
        else:
            final_message = str(content)

        return ChatResponse(response=final_message)

    except Exception as e:
        return ChatResponse(response=f"Error: {str(e)}")