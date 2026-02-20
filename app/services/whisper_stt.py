import whisper
from pathlib import Path

model = whisper.load_model("tiny")

def speech_to_text(audio_path: str) -> str:
    audio_path = str(Path(audio_path).resolve())

    if not Path(audio_path).exists():
        raise RuntimeError(f"Audio file does not exist: {audio_path}")

    result = model.transcribe(audio_path)
    return result["text"].strip()
