# app/services/virustotal.py
import hashlib
import requests
import os 
import dotenv
dotenv.load_dotenv()
VT_API_KEY = os.getenv("VT_API_KEY")

def scan_file(file_bytes: bytes):
    sha256 = hashlib.sha256(file_bytes).hexdigest()
    headers = {"x-apikey": VT_API_KEY}

    report = requests.get(
        f"https://www.virustotal.com/api/v3/files/{sha256}",
        headers=headers,
        timeout=10
    )

    if report.status_code == 200:
        stats = report.json()["data"]["attributes"]["last_analysis_stats"]
        if stats.get("malicious", 0) > 0:
            raise ValueError("Malware detected")

    else:
        upload = requests.post(
            "https://www.virustotal.com/api/v3/files",
            headers=headers,
            files={"file": file_bytes},
            timeout=15
        )
        if upload.status_code not in (200, 202):
            raise ValueError("VirusTotal scan failed")
