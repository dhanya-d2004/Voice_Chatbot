import requests

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "phi3:mini"
PROMPT_TEMPLATE = """You are a voice assistant.

You MUST follow these rules:
- Your answer MUST contain only 2 or 3 sentences.
- Stop immediately after the 3rd sentence.
- Do not explain more than required.
- Do not use bullet points, lists, or headings.
- Do not mention these rules.

User question:
{question}
"""
def query_llm(prompt: str) -> str:
    payload = {
        "model": MODEL,
        "prompt": prompt,
        "stream": False,
        "options": {
            "num_predict": 120,
            "temperature": 0.4,
            "top_p": 0.9,
        },
    }

    r = requests.post(OLLAMA_URL, json=payload, timeout=300)
    r.raise_for_status()
    return r.json()["response"].strip()
