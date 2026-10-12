"""Turns the nudge into audio.

local      -> pyttsx3 (offline; uses the voices installed in Windows/macOS/Linux)
elevenlabs -> ElevenLabs multilingual voice (needs ELEVENLABS_API_KEY)
none       -> no audio, text only
"""
from pathlib import Path

import requests

from config import (AUDIO_DIR, ELEVENLABS_API_KEY, ELEVENLABS_MODEL,
                    ELEVENLABS_VOICE_ID, TTS_BACKEND)


def speak(text: str, stem: str, backend: str = None) -> Path | None:
    backend = (backend or TTS_BACKEND).lower()
    if backend == "none":
        return None
    if backend == "elevenlabs":
        return _elevenlabs(text, AUDIO_DIR / f"{stem}-elevenlabs.mp3")
    return _local(text, AUDIO_DIR / f"{stem}-local.wav")


def _local(text: str, out: Path) -> Path:
    import pyttsx3

    engine = pyttsx3.init()
    engine.setProperty("rate", 150)  # a little slower than default, easier to follow
    engine.save_to_file(text, str(out))
    engine.runAndWait()
    return out


def _elevenlabs(text: str, out: Path) -> Path:
    if not ELEVENLABS_API_KEY:
        raise RuntimeError("TTS_BACKEND=elevenlabs but ELEVENLABS_API_KEY is empty in .env")
    r = requests.post(
        f"https://api.elevenlabs.io/v1/text-to-speech/{ELEVENLABS_VOICE_ID}",
        headers={"xi-api-key": ELEVENLABS_API_KEY, "accept": "audio/mpeg"},
        json={"text": text, "model_id": ELEVENLABS_MODEL,
              "voice_settings": {"stability": 0.6, "similarity_boost": 0.8}},
        timeout=120,
    )
    r.raise_for_status()
    out.write_bytes(r.content)
    return out
