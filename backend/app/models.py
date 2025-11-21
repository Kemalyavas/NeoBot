from pydantic import BaseModel

class StartChatRequest(BaseModel):
    pass

class ChatMessageRequest(BaseModel):
    thread_id: str
    message: str

class ChatResponse(BaseModel):
    response: str
