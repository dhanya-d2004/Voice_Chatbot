from fastapi import FastAPI
from app.api.voice import router as voice_router
from app.api.auth import router as auth_router
from app.api.text import router as text_router
from fastapi.middleware.cors import CORSMiddleware
from app.api import auth, voice_ws 
app = FastAPI(title="Voice AI")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",  # frontend
    ],
    allow_credentials=True,
    allow_methods=["*"],  # includes OPTIONS
    allow_headers=["*"],
)

@app.get("/")
def root():
    return {"service": "Voice AI", "status": "running"}

app.include_router(text_router)
app.include_router(auth_router)
app.include_router(voice_router)
app.include_router(voice_ws.router)