import uuid
from pathlib import Path
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.deps import get_db
from app.services.deps import get_current_user
from app.services.whisper_stt import speech_to_text
from app.services.ollama_llm import query_llm
from app.services.piper_tts import text_to_speech

router = APIRouter(prefix="/api")

TEMP_DIR = Path("app/temp")
TEMP_DIR.mkdir(parents=True, exist_ok=True)

@router.post("/voice-chat")
async def voice_chat(
    audio: UploadFile = File(...),
    user = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if not audio.filename:
        raise HTTPException(status_code=400, detail="No audio file provided")

    # 1️⃣ Save file
    audio_path = TEMP_DIR / f"{uuid.uuid4()}.wav"

    with open(audio_path, "wb") as f:
        f.write(await audio.read())

    if not audio_path.exists():
        raise HTTPException(status_code=500, detail="Failed to save audio file")

    # 2️⃣ Whisper STT
    user_text = speech_to_text(str(audio_path))

    # 3️⃣ LLM
    llm_reply = query_llm(user_text)

    # 4️⃣ TTS
    reply_audio_path = text_to_speech(llm_reply)

    return {
        "transcript": user_text,
        "reply_text": llm_reply,
        "reply_audio": reply_audio_path,
    }
