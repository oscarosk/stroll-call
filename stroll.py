"""Stroll Call - command line.

  python stroll.py today            make (or replay) today's spoken walk nudge
  python stroll.py today --force    make a fresh one even if today's exists
  python stroll.py log --minutes 20 --felt good --note "stopped at the nursery"
  python stroll.py history
"""
import argparse
from datetime import date

import tracing
from config import OLLAMA_MODEL, TTS_BACKEND, load_profile
from memory import get_memory
from nudge import generate
from speak import speak


def make_today(force: bool = False, backend: str = None) -> dict:
    profile = load_profile()
    mem = get_memory(profile["name"])
    today = date.today().isoformat()

    with tracing.agent_run("stroll-call daily nudge") as run:
        run.set_data("person", profile["name"])
        run.set_data("memory.backend", mem.backend)

        existing = mem.get(today)
        if existing and existing.get("nudge") and not force:
            return existing

        with tracing.span("db", "load recent walks"):
            history = mem.recent(5, before=today)

        with tracing.span("gen_ai.chat", f"chat {OLLAMA_MODEL}") as s:
            try:
                result = generate(profile, history, today)
            except Exception as e:  # surface model failures in Sentry
                tracing.capture(e)
                raise
            s.set_data("gen_ai.system", "ollama")
            s.set_data("gen_ai.request.model", result["model"])
            s.set_data("gen_ai.usage.input_tokens", result["input_tokens"])
            s.set_data("gen_ai.usage.output_tokens", result["output_tokens"])
            s.set_data("latency_ms", result["latency_ms"])

        audio = None
        with tracing.span("tts", f"speak via {backend or TTS_BACKEND}"):
            try:
                audio = speak(result["text"], today, backend)
            except Exception as e:  # never lose the text because the voice failed
                tracing.capture(e)
                print(f"[voice failed, text still saved] {e}")

        meta = {k: result[k] for k in ("model", "input_tokens", "output_tokens", "latency_ms")}
        meta["audio"] = audio.name if audio else None
        with tracing.span("db", "save nudge"):
            mem.save_nudge(today, result["text"], meta)

    tracing.flush()
    return mem.get(today)


def main():
    p = argparse.ArgumentParser(description="Stroll Call")
    sub = p.add_subparsers(dest="cmd", required=True)
    t = sub.add_parser("today")
    t.add_argument("--force", action="store_true")
    t.add_argument("--voice", choices=["local", "elevenlabs", "none"])
    lg = sub.add_parser("log")
    lg.add_argument("--minutes", type=int, required=True)
    lg.add_argument("--felt", default="good", help="e.g. good / tired / great / sore knee")
    lg.add_argument("--note", default="")
    lg.add_argument("--date", default=date.today().isoformat())
    sub.add_parser("history")
    args = p.parse_args()

    tracing.init()
    profile = load_profile()
    mem = get_memory(profile["name"])

    if args.cmd == "today":
        row = make_today(args.force, args.voice)
        print(f"\n{row['nudge']}\n")
        m = row.get("meta", {})
        print(f"model={m.get('model')}  tokens in/out={m.get('input_tokens')}/{m.get('output_tokens')}"
              f"  latency={m.get('latency_ms')} ms  audio={m.get('audio')}")
    elif args.cmd == "log":
        mem.log_walk(args.date, args.minutes, args.felt, args.note)
        print(f"Logged {args.minutes} min walk for {profile['name']} on {args.date}.")
    elif args.cmd == "history":
        for r in mem.recent(30):
            w = r.get("walk")
            walked = f"{w['minutes']} min, {w['felt']}" if w else "not logged"
            print(f"{r['date']}  [{walked}]  {r.get('nudge') or ''}")


if __name__ == "__main__":
    main()
