import tempfile
import numpy as np
import soundfile as sf
from uuid import UUID
from fastapi import APIRouter, WebSocket
from starlette.websockets import WebSocketDisconnect

from app.db.session import SessionLocal
from app.models.conversation import Conversation
from app.models.message import Message
from app.services.deps import get_current_user_ws
from app.services.whisper_stt import speech_to_text
from app.services.ollama_llm import query_llm
from app.services.piper_tts import text_to_speech

router = APIRouter(prefix="/api")
SAMPLE_RATE = 16000


@router.websocket("/voice-chat/ws")
async def voice_chat_ws(websocket: WebSocket):
    user = get_current_user_ws(websocket)
    await websocket.accept()

    db = SessionLocal()
    audio_chunks = []

    try:
        # 🔑 conversation_id is OPTIONAL
        conv_raw = websocket.query_params.get("conversation_id")
        conversation = None

        if conv_raw:
            try:
                conv_id = UUID(conv_raw)
                conversation = (
                    db.query(Conversation)
                    .filter(
                        Conversation.id == conv_id,
                        Conversation.user_id == user.id
                    )
                    .first()
                )
            except ValueError:
                conversation = None

        # ✅ auto-create conversation if missing
        if not conversation:
            conversation = Conversation(user_id=user.id)
            db.add(conversation)
            db.commit()
            db.refresh(conversation)

            await websocket.send_json({
                "type": "conversation_created",
                "conversation_id": str(conversation.id)
            })

        # 🎙️ receive audio
        while True:
            msg = await websocket.receive()

            if msg.get("text") == "END":
                break

            if "bytes" in msg:
                audio_chunks.append(
                    np.frombuffer(msg["bytes"], dtype=np.float32)
                )

        if not audio_chunks:
            return

        audio = np.concatenate(audio_chunks)

        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
            sf.write(f.name, audio, SAMPLE_RATE)
            wav_path = f.name

        # 🗣️ STT (force English)
        transcript = speech_to_text(wav_path)

        if len(transcript.strip()) < 2:
            return

        # 💾 store user voice message
        db.add(Message(
            conversation_id=conversation.id,
            role="user",
            content=transcript
        ))
        db.commit()

        await websocket.send_json({
            "type": "user_message",
            "text": transcript
        })

        # 🧠 build memory
        history = (
            db.query(Message)
            .filter(Message.conversation_id == conversation.id)
            .order_by(Message.created_at)
            .all()
        )

        prompt = "\n".join(
            f"{m.role.capitalize()}: {m.content}" for m in history
        ) + "\nAssistant:"

        # 🤖 LLM
        reply_text = query_llm(prompt)

        db.add(Message(
            conversation_id=conversation.id,
            role="assistant",
            content=reply_text
        ))
        db.commit()

        await websocket.send_json({
            "type": "assistant_message",
            "text": reply_text
        })

        # 🔊 TTS
        audio_path = text_to_speech(reply_text)
        with open(audio_path, "rb") as f:
            await websocket.send_bytes(f.read())

    except WebSocketDisconnect:
        pass
    finally:
        db.close()
