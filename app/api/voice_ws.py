import tempfile
import numpy as np
import soundfile as sf
from fastapi import APIRouter, WebSocket
from starlette.websockets import WebSocketDisconnect

from app.services.deps import get_current_user_ws
from app.services.whisper_stt import speech_to_text
from app.services.ollama_llm import query_llm
from app.services.piper_tts import text_to_speech

router = APIRouter(prefix="/api")
SAMPLE_RATE = 16000


@router.websocket("/voice-chat/ws")
async def voice_chat_ws(websocket: WebSocket):
    # 1️⃣ Authenticate
    user = get_current_user_ws(websocket)

    await websocket.accept()

    audio_chunks = []

    try:
        while True:
            msg = await websocket.receive()

            if "text" in msg and msg["text"] == "END":
                break

            if "bytes" not in msg:
                continue

            chunk = np.frombuffer(msg["bytes"], dtype=np.float32)
            audio_chunks.append(chunk)

        if not audio_chunks:
            return  # client closed early

        audio = np.concatenate(audio_chunks)

        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
            sf.write(f.name, audio, SAMPLE_RATE)
            wav_path = f.name

        # STT
        transcript = speech_to_text(wav_path)

        # client may have closed while whisper was running
        await websocket.send_json({
            "type": "transcript",
            "text": transcript,
        })

        # LLM
        reply_text = query_llm(transcript)
        await websocket.send_json({
            "type": "reply_text",
            "text": reply_text,
        })

        # TTS
        reply_audio_path = text_to_speech(reply_text)
        with open(reply_audio_path, "rb") as f:
            await websocket.send_bytes(f.read())

    except WebSocketDisconnect:
        # ✅ client disconnected normally — DO NOTHING
        pass

    except Exception as e:
        # ✅ only log — do NOT send on closed socket
        print("WS error:", e)

    finally:
        # ✅ close only if still open
        try:
            await websocket.close()
        except Exception:
            pass
