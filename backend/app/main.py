from fastapi import FastAPI
from pydantic import BaseModel

from app.agent import agent

# Create FastAPI application
app = FastAPI(title="Google Drive Search Agent")


# Request body schema
class ChatRequest(BaseModel):
    message: str


# Response body schema
class ChatResponse(BaseModel):
    response: str


@app.get("/")
def root():
    return {"message": "Google Drive Search Agent is running!"}

@app.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest):
    try:
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