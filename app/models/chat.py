from pydantic import BaseModel
from typing import List

class ChatMessage(BaseModel):
    role: str   # "user" | "assistant"
    content: str

class TextChatRequest(BaseModel):
    conversation_id: str
    messages: List[ChatMessage]
