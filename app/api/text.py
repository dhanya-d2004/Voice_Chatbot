from app.models.conversation import Conversation
from app.models.message import Message
from app.db.deps import get_db
from app.services.ollama_llm import query_llm
from app.services.deps import get_current_user
from app.models.chat import TextChatRequest
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session  
from uuid import UUID

router = APIRouter(prefix="/api", tags=["text"])
@router.post("/text-chat")
def text_chat(
    data: TextChatRequest,
    user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
# ✅ NEW (safe UUID handling)
    conversation = None

    if data.conversation_id:
        try:
            conv_id = UUID(str(data.conversation_id))
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid conversation_id")

        conversation = (
            db.query(Conversation)
            .filter(
                Conversation.id == conv_id,
                Conversation.user_id == user.id
            )
            .first()
        )

        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")

    else:
        conversation = Conversation(user_id=user.id)
        db.add(conversation)
        db.flush()  # 🔑 generate conversation.id

    # 2️⃣ Store user message
    user_message = Message(
        conversation_id=conversation.id,
        role="user",
        content=data.messages[-1].content,
    )
    db.add(user_message)
    db.flush()

    # 3️⃣ Load conversation history from DB
    history = (
        db.query(Message)
        .filter(Message.conversation_id == conversation.id)
        .order_by(Message.created_at)
        .all()
    )

    # 4️⃣ Build prompt from DB history
    prompt_parts = []
    for msg in history:
        if msg.role == "user":
            prompt_parts.append(f"User: {msg.content}")
        else:
            prompt_parts.append(f"Assistant: {msg.content}")

    prompt = "\n".join(prompt_parts) + "\nAssistant:"

    # 5️⃣ Query LLM
    reply = query_llm(prompt)

    # 6️⃣ Store assistant reply
    assistant_message = Message(
        conversation_id=conversation.id,
        role="assistant",
        content=reply,
    )
    db.add(assistant_message)
    db.commit()

    return {
        "conversation_id": str(conversation.id),
        "reply": reply,
    }
