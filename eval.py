"""Evaluates the nudges a model writes, so the blog post has real numbers.

  python eval.py --model gemma3:4b --runs 3
  python eval.py --model gemma3:1b --runs 3     (compare a smaller model)

For each scenario it generates nudges, runs automatic checks, and writes
results/eval_<model>.csv with empty columns for YOUR human ratings.
"""
import argparse
import csv
import re
import statistics
from datetime import date, timedelta

from config import RESULTS_DIR, load_profile
from nudge import generate

TODAY = date.today()


def _day(n):
    return (TODAY - timedelta(days=n)).isoformat()


SCENARIOS = {
    "first_day": [],
    "good_streak": [
        {"date": _day(1), "walk": {"minutes": 20, "felt": "great", "note": "chatted with the nursery owner"}},
        {"date": _day(2), "walk": {"minutes": 18, "felt": "good", "note": ""}},
    ],
    "tired_yesterday": [
        {"date": _day(1), "walk": {"minutes": 8, "felt": "tired", "note": "knee hurt on the way back"}},
    ],
    "skipped_two_days": [
        {"date": _day(1), "walk": None},
        {"date": _day(2), "walk": None},
        {"date": _day(3), "walk": {"minutes": 15, "felt": "good", "note": ""}},
    ],
}


def auto_checks(text: str, profile: dict, history: list) -> dict:
    low = text.lower()
    words = len(text.split())
    place_hits = [p["name"] for p in profile["places"] if _key(p["name"]) in low]
    avoid_hits = [a for a in profile["avoid"] if _key(a) in low]
    return {
        "words": words,
        "length_ok": 40 <= words <= 80,
        "no_markdown": not re.search(r"[*#`]|^\s*-", text, re.M),
        "uses_known_place": bool(place_hits),
        "places_mentioned": "; ".join(place_hits),
        "mentions_avoid_item": bool(avoid_hits),
        "refers_to_history": (not history) or bool(re.search(r"yesterday|last time|last walk|other day|few days", low)),
    }


def _key(phrase: str) -> str:
    """Most distinctive word(s) of a place/avoid phrase for a loose match."""
    stop = {"the", "a", "an", "of", "by", "inside", "behind", "after", "in", "walking", "hot", "weather", "am"}
    words = [w for w in re.findall(r"[a-z]+", phrase.lower()) if w not in stop]
    return " ".join(words[-2:]) if words else phrase.lower()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default=None)
    ap.add_argument("--runs", type=int, default=3, help="nudges per scenario")
    args = ap.parse_args()

    profile = load_profile()
    rows = []
    for name, history in SCENARIOS.items():
        for i in range(args.runs):
            r = generate(profile, history, TODAY.isoformat(), model=args.model)
            checks = auto_checks(r["text"], profile, history)
            rows.append({"scenario": name, "run": i + 1, **checks,
                         "latency_ms": r["latency_ms"], "input_tokens": r["input_tokens"],
                         "output_tokens": r["output_tokens"], "model": r["model"], "text": r["text"],
                         # fill these in yourself after listening / reading:
                         "human_natural_1to5": "", "human_safe_yes_no": "", "would_follow_yes_no": ""})
            print(f"[{name} #{i+1}] {checks['words']}w {r['latency_ms']}ms  {r['text'][:90]}...")

    model = rows[0]["model"].replace(":", "_").replace("/", "_")
    out = RESULTS_DIR / f"eval_{model}.csv"
    with open(out, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)

    n = len(rows)
    pct = lambda k: f"{sum(1 for r in rows if r[k]) / n:.0%}"
    print(f"\n=== {rows[0]['model']} - {n} nudges ===")
    print(f"length 40-80 words : {pct('length_ok')}")
    print(f"no markdown        : {pct('no_markdown')}")
    print(f"uses a known place : {pct('uses_known_place')}")
    print(f"mentions AVOID item: {pct('mentions_avoid_item')}   (want 0%)")
    print(f"refers to history  : {pct('refers_to_history')}")
    print(f"median latency     : {statistics.median(r['latency_ms'] for r in rows)} ms")
    print(f"median output toks : {statistics.median(r['output_tokens'] or 0 for r in rows)}")
    print(f"\nSaved {out}  -> now fill in the three human_* columns.")


if __name__ == "__main__":
    main()
