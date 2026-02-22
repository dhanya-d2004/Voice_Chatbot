# app/api/document.py
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from sqlalchemy.orm import Session
from uuid import UUID
from pathlib import Path
from app.db.deps import get_db
from app.services.deps import get_current_user
from app.models.conversation import Conversation
from app.models.message import Message
from app.services.virustotal import scan_file
from app.services.document_parser import extract_text
from app.services.chunker import chunk_text
from app.services.embeddings import embed

router = APIRouter(prefix="/api", tags=["documents"])

# app/api/document.py

MAX_SIZE = 15 * 1024 * 1024  # 15MB

ALLOWED_EXTENSIONS = {".pdf", ".docx", ".pptx", ".txt", ".jpg", ".jpeg", ".png"}

def is_allowed_file(file: UploadFile) -> bool:
    content_type = (file.content_type or "").lower()
    suffix = Path(file.filename).suffix.lower()

    # MIME-based checks
    if content_type.startswith("application/pdf"):
        return True
    if content_type.startswith("text/plain"):
        return True
    if content_type.startswith("image/jpeg"):
        return True
    if content_type.startswith("image/png"):
        return True
    if "wordprocessingml" in content_type:
        return True
    if "presentationml" in content_type:
        return True

    # Fallback for application/octet-stream
    if content_type == "application/octet-stream":
        return suffix in ALLOWED_EXTENSIONS

    return False

@router.post("/document/upload")
def upload_document(
    file: UploadFile = File(...),
    conversation_id: UUID | None = None,
    user=Depends(get_current_user),
    db: Session = Depends(get_db),
    ):
    # 1️⃣ Validate
    if not is_allowed_file(file):
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type: {file.content_type}"
        )
    data = file.file.read()
    if len(data) > MAX_SIZE:
        raise HTTPException(400, "File exceeds 15MB")

    # 2️⃣ Virus scan
    try:
        scan_file(data)
    except ValueError as e:
        raise HTTPException(400, str(e))

    # 3️⃣ Conversation
    conversation = None
    if conversation_id:
        conversation = (
            db.query(Conversation)
            .filter(
                Conversation.id == conversation_id,
                Conversation.user_id == user.id
            )
            .first()
        )
        if not conversation:
            raise HTTPException(404, "Conversation not found")
    else:
        conversation = Conversation(user_id=user.id)
        db.add(conversation)
        db.flush()

    # 4️⃣ Extract + chunk
    text = extract_text(data, file.content_type, file.filename)
    chunks = chunk_text(text)

    if not chunks:
        raise HTTPException(400, "No text extracted")

    # 5️⃣ Embed
    embeddings = embed(chunks)

    # 6️⃣ Store chunks as messages
    for chunk, vector in zip(chunks, embeddings):
        db.add(Message(
            conversation_id=conversation.id,
            role="document",
            content=chunk,
            embedding=vector
        ))

    db.commit()

    return {
        "conversation_id": str(conversation.id),
        "chunks_stored": len(chunks),
        "filename": file.filename
    }
