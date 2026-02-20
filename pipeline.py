import subprocess
import json
import requests
from pathlib import Path

AUDIO_INPUT = "audio/input.wav"
AUDIO_OUTPUT = "audio/output.wav"
WHISPER_MODEL = "tiny"
OLLAMA_MODEL = "phi3:mini"
PIPER_MODEL = "/home/ubuntu/piper/voices/en_US-lessac-medium.onnx"

# ---------------------------
# 1. Whisper: speech → text
# ---------------------------
import whisper

whisper_model = whisper.load_model(WHISPER_MODEL)

def transcribe(audio_path: str) -> str:
    result = whisper_model.transcribe(audio_path)
    return result["text"].strip()


# ---------------------------
# 2. Ollama: text → response
# ---------------------------
def ask_ollama(prompt: str) -> str:
    response = requests.post(
        "http://localhost:11434/api/generate",
        json={
            "model": OLLAMA_MODEL,
            "prompt": prompt,
            "stream": True
        },
        stream=True
    )

    response.raise_for_status()

    chunks = []
    for line in response.iter_lines():
        if not line:
            continue

        data = json.loads(line.decode("utf-8"))

        if "response" in data:
            chunks.append(data["response"])

        if data.get("done"):
            break

    return "".join(chunks).strip()
# ---------------------------
# 3. Piper: text → speech
# ---------------------------
def speak(text: str, output_path: str):
    process = subprocess.Popen(
        [
            "piper",
            "--model", PIPER_MODEL,
            "--output_file", output_path
        ],
        stdin=subprocess.PIPE
    )

    process.stdin.write(text.encode("utf-8"))
    process.stdin.close()
    process.wait()

# ---------------------------
# Main pipeline
# ---------------------------
if __name__ == "__main__":
    print("🎙 Transcribing audio...")
    text = transcribe(AUDIO_INPUT)
    print("📝 User said:", text)

    print("🤖 Asking Ollama...")
    reply = ask_ollama(text)
    print("💬 Ollama replied:", reply)

    print("🔊 Generating speech...")
    speak(reply, AUDIO_OUTPUT)

    print("✅ Done! Output saved to", AUDIO_OUTPUT)
