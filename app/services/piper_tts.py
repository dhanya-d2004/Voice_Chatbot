import subprocess
import uuid
from pathlib import Path

PIPER_MODEL = "/home/ubuntu/piper/voices/en_US-lessac-medium.onnx"
OUTPUT_DIR = Path("app/temp")

OUTPUT_DIR.mkdir(exist_ok=True)

def text_to_speech(text: str) -> str:
    output_file = OUTPUT_DIR / f"{uuid.uuid4()}.wav"

    process = subprocess.run(
        [
            "piper",
            "--model", PIPER_MODEL,
            "--output_file", str(output_file)
        ],
        input=text.encode("utf-8"),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=True,
    )

    return str(output_file)
