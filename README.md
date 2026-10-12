# Stroll Call

A screen-free voice walk companion for older adults. Every morning a **local open-weight model** writes a short, personal walk suggestion, remembers how yesterday's walk went, and reads it aloud. The person walking never touches a screen.

- Runs on an ordinary laptop with [Ollama](https://ollama.com) and Gemma. No cloud model, no subscription.
- Their routine, places, and health notes stay at home.
- Works in any language the model and voice support: change `"language"` in `profile.json`.

Built for the DEV Hacktoberfest Open-Source AI Challenge, Week 1: Touch Grass (Oct 5–11, 2026).

## Setup (Windows 11, 8 GB RAM)

1. Install Ollama from https://ollama.com, then in a terminal:
   ```
   ollama pull gemma3:4b
   ollama run gemma3:4b "hello"
   ```
   If that is slow on your machine, use `gemma3:1b` and set `OLLAMA_MODEL=gemma3:1b` in `.env`.
2. Install Python 3.10+, then in this folder:
   ```
   python -m venv .venv
   .venv\Scripts\activate
   pip install -r requirements.txt
   copy .env.example .env
   copy profile.example.json profile.json
   ```
3. Edit `profile.json` with the real person: name, language, mobility, nearby places, people, likes, and things to avoid.

## Use

```
python stroll.py today                  # write + speak today's walk (saved in audio/)
python stroll.py log --minutes 20 --felt good --note "stopped at the nursery"
python stroll.py history
python app.py                           # simple page at http://localhost:5000
```

The web page has one big button to play today's walk, plus a short form to log the walk afterwards.

## Optional partner tech

| Feature | Turn on in `.env` |
|---|---|
| ElevenLabs multilingual voice | `TTS_BACKEND=elevenlabs` and `ELEVENLABS_API_KEY` |
| MongoDB Atlas walk memory | `MONGODB_URI` (otherwise `data/walks.json`) |
| Sentry agent tracing (latency, tokens, errors) | `SENTRY_DSN` |

## Evaluate

```
python eval.py --model gemma3:4b --runs 3
python eval.py --model gemma3:1b --runs 3
```

This writes `results/eval_<model>.csv` with automatic checks (length, uses a real place, avoids unsafe places, remembers history, latency, tokens) and empty columns for your own ratings.

## Notes

Any commits made after the submission deadline (Oct 11, 2026, 11:59 PM PDT) are listed here.
