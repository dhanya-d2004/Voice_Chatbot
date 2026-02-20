from pydantic import BaseModel
from typing import List, Optional
from uuid import UUID
from typing_extensions import Literal


class ChatMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str


class TextChatRequest(BaseModel):
    conversation_id: Optional[UUID] = None
    messages: List[ChatMessage]
