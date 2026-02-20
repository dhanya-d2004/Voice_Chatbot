from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.db.deps import get_db
from app.services.deps import get_current_user
from app.services.ollama_llm import query_llm
from app.models.chat import TextChatRequest

router = APIRouter(prefix="/api", tags=["text"])


@router.post("/text-chat")
def text_chat(
    data: TextChatRequest,
    user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    ChatGPT-style text endpoint.
    Uses full conversation history as context.
    """

    if not data.messages:
        raise HTTPException(status_code=400, detail="Conversation is empty")

    # Build prompt with context
    prompt_parts: List[str] = []

    for msg in data.messages:
        if msg.role == "user":
            prompt_parts.append(f"User: {msg.content}")
        elif msg.role in ("assistant", "bot"):
            prompt_parts.append(f"Assistant: {msg.content}")

    prompt = "\n".join(prompt_parts) + "\nAssistant:"

    reply = query_llm(prompt)

    return {
        "conversation_id": data.conversation_id,
        "reply": reply,
    }
