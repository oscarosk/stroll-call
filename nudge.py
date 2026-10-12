"""Writes one short spoken walk suggestion with a local open-weight model (Ollama)."""
import re
import time

import requests

from config import OLLAMA_MODEL, OLLAMA_URL

SYSTEM = """You are Stroll Call, a warm voice companion that helps an older adult go for a short walk.
You write ONE spoken message that will be read aloud by a text-to-speech voice. They never look at a screen.

Rules:
- Write in {language}. Speak directly to {name}, warmly, like a caring grandchild. Simple words, short sentences.
- 40 to 70 words. No lists, no emojis, no markdown, no headings. Plain sentences only.
- Suggest ONE route using ONLY places from the PLACES list. Never invent places or people.
- Include one thing to notice with the senses (something to look at, listen to, or smell).
- Include one small friendly moment with a person from the PEOPLE list, or a rest on a bench.
- Respect their mobility. Never suggest anything from the AVOID list.
- Suggest a length close to their usual walk, nudging gently towards the goal. Never push if they felt tired recently.
- If there is a recent walk in HISTORY, refer to it briefly and kindly in the first sentence, and vary today's route.
- No medical advice. End with a short encouraging line."""


def _history_text(history: list) -> str:
    if not history:
        return "No walks recorded yet. This is the first day."
    lines = []
    for h in history:
        w = h.get("walk")
        if w:
            lines.append(f"- {h['date']}: walked {w['minutes']} min, felt {w['felt']}. Note: {w.get('note') or 'none'}")
        else:
            lines.append(f"- {h['date']}: did not walk (or it was not logged).")
    return "\n".join(lines)


def build_messages(profile: dict, history: list, today: str) -> list:
    places = "\n".join(f"- {p['name']} ({p['note']})" for p in profile["places"])
    user = f"""TODAY: {today}
NAME: {profile['name']} (age {profile.get('age', 'unknown')})
MOBILITY: {profile['mobility']}
USUAL WALK: {profile['usual_minutes']} minutes. GOAL: {profile['goal_minutes']} minutes.
BEST TIME: {profile.get('best_time', 'morning')}
HOME: {profile.get('home', '')}
PLACES:
{places}
PEOPLE: {', '.join(profile['people'])}
LIKES: {', '.join(profile['likes'])}
AVOID: {', '.join(profile['avoid'])}
HISTORY (most recent first):
{_history_text(history)}

Write today's spoken walk message now."""
    system = SYSTEM.format(language=profile.get("language", "English"), name=profile["name"])
    return [{"role": "system", "content": system}, {"role": "user", "content": user}]


def clean(text: str) -> str:
    text = re.sub(r"[*_#`>]+", "", text)          # strip markdown symbols
    text = re.sub(r"^\s*[-•]\s*", "", text, flags=re.M)
    text = re.sub(r"\s+", " ", text)
    return text.strip().strip('"').strip()


def generate(profile: dict, history: list, today: str, model: str = None, temperature: float = 0.8) -> dict:
    model = model or OLLAMA_MODEL
    t0 = time.perf_counter()
    r = requests.post(
        f"{OLLAMA_URL}/api/chat",
        json={
            "model": model,
            "messages": build_messages(profile, history, today),
            "stream": False,
            "options": {"temperature": temperature},
        },
        timeout=600,
    )
    r.raise_for_status()
    data = r.json()
    return {
        "text": clean(data["message"]["content"]),
        "model": model,
        "input_tokens": data.get("prompt_eval_count"),
        "output_tokens": data.get("eval_count"),
        "latency_ms": round((time.perf_counter() - t0) * 1000),
    }
