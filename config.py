"""Central settings. Everything is read from .env so nothing secret lives in code."""
import json
import os
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent
load_dotenv(ROOT / ".env")

# Local open-weight model served by Ollama
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "gemma3:4b")

# Voice: "local" (offline, pyttsx3 / Windows voices), "elevenlabs", or "none" (text only)
TTS_BACKEND = os.getenv("TTS_BACKEND", "local").lower()
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY", "")
ELEVENLABS_VOICE_ID = os.getenv("ELEVENLABS_VOICE_ID", "21m00Tcm4TlvDq8ikWAM")
ELEVENLABS_MODEL = os.getenv("ELEVENLABS_MODEL", "eleven_multilingual_v2")

# Walk memory: MongoDB Atlas if a URI is set, otherwise a local JSON file
MONGODB_URI = os.getenv("MONGODB_URI", "")
MONGODB_DB = os.getenv("MONGODB_DB", "stroll_call")

# Agent tracing (optional)
SENTRY_DSN = os.getenv("SENTRY_DSN", "")

PROFILE_PATH = ROOT / "profile.json"
EXAMPLE_PROFILE_PATH = ROOT / "profile.example.json"
DATA_DIR = ROOT / "data"
AUDIO_DIR = ROOT / "audio"
RESULTS_DIR = ROOT / "results"

for d in (DATA_DIR, AUDIO_DIR, RESULTS_DIR):
    d.mkdir(exist_ok=True)


def load_profile() -> dict:
    path = PROFILE_PATH if PROFILE_PATH.exists() else EXAMPLE_PROFILE_PATH
    with open(path, encoding="utf-8") as f:
        return json.load(f)
