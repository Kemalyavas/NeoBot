from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from app.models import StartChatRequest, ChatMessageRequest, ChatResponse
from app.assistant import create_thread, add_message_to_thread, run_assistant
from app.tools import MOCK_PRODUCTS

app = FastAPI(title="NeoBot MVP Backend")

# CORS Configuration (Allow React Frontend)
origins = [
    "http://localhost:5173", # Vite default port
    "http://localhost:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/api/products")
async def get_products():
    """
    Returns the current state of products (including live discounts).
    """
    return MOCK_PRODUCTS

@app.post("/api/chat/start")
async def start_chat():
    """
    Starts a new chat session (thread).
    """
    try:
        thread = create_thread()
        return {"thread_id": thread.id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/chat/message", response_model=ChatResponse)
async def send_message(request: ChatMessageRequest):
    """
    Sends a message to the assistant and gets a response.
    """
    try:
        add_message_to_thread(request.thread_id, request.message)
        response_text = run_assistant(request.thread_id)
        return {"response": response_text}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
