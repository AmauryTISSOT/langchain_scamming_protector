import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.api.routes import router
from app.api.session_manager import SessionManager
from app.core.config import load_config

api_key = load_config()

app = FastAPI(title="Langchain Scamming Protector")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

sounds_dir = os.path.join(os.path.dirname(__file__), "app", "tools", "sounds")
app.mount("/static/sounds", StaticFiles(directory=sounds_dir), name="sounds")

session_manager = SessionManager(api_key)
app.state.session_manager = session_manager

app.include_router(router)
