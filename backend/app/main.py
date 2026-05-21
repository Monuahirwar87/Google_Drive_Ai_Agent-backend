from fastapi import FastAPI,HTTPException
from fastapi.middleware.cors import CORSMiddleware  # 🆕 Import middleware
from pydantic import BaseModel
from pyparsing import Optional
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

class ChatRequest(BaseModel):
    message: str
    folder_id: Optional[str] = None

@app.post("/chat")
async def chat_endpoint(req: ChatRequest):
    try:
        # Pass folder scope parameter down safely into prompt injection structure
        target_folder = req.folder_id if req.folder_id and req.folder_id != "None" else "all_drive"
        response = agent.invoke({"input": req.message, "folder_id": target_folder})
        return {"response": response.get("output", "No response generated.")}
    except Exception as e:
        error_msg = str(e)
        if "429" in error_msg or "RESOURCE_EXHAUSTED" in error_msg:
            raise HTTPException(status_code=429, detail="Gemini Rate Limit Exceeded. Please try again in 60 seconds.")
        raise HTTPException(status_code=500, detail=error_msg)

@app.get("/folders")
async def folders_endpoint():
    from app.tools import get_all_folders
    try:
        folders = get_all_folders()
        return {"folders": folders}
    except Exception as e:
        return {"folders": []}