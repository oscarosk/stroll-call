"""Walk memory: one record per day with the nudge that was spoken and how the walk went.

Uses MongoDB Atlas when MONGODB_URI is set, otherwise data/walks.json.
"""
import json
from datetime import datetime, timezone

from config import DATA_DIR, MONGODB_DB, MONGODB_URI


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


class JsonMemory:
    backend = "json"

    def __init__(self, person: str):
        self.person = person
        self.path = DATA_DIR / "walks.json"
        if not self.path.exists():
            self.path.write_text("[]", encoding="utf-8")

    def _load(self) -> list:
        return json.loads(self.path.read_text(encoding="utf-8"))

    def _save(self, rows: list):
        self.path.write_text(json.dumps(rows, indent=2, ensure_ascii=False), encoding="utf-8")

    def get(self, date: str):
        for r in self._load():
            if r["person"] == self.person and r["date"] == date:
                return r
        return None

    def save_nudge(self, date: str, nudge: str, meta: dict):
        rows = self._load()
        row = next((r for r in rows if r["person"] == self.person and r["date"] == date), None)
        if row is None:
            row = {"person": self.person, "date": date, "walk": None}
            rows.append(row)
        row.update({"nudge": nudge, "meta": meta, "created_at": _now()})
        self._save(rows)

    def log_walk(self, date: str, minutes: int, felt: str, note: str):
        rows = self._load()
        row = next((r for r in rows if r["person"] == self.person and r["date"] == date), None)
        if row is None:
            row = {"person": self.person, "date": date, "nudge": None, "meta": {}}
            rows.append(row)
        row["walk"] = {"minutes": minutes, "felt": felt, "note": note, "logged_at": _now()}
        self._save(rows)

    def recent(self, n: int = 5, before: str = None) -> list:
        rows = [r for r in self._load() if r["person"] == self.person]
        if before:
            rows = [r for r in rows if r["date"] < before]
        return sorted(rows, key=lambda r: r["date"], reverse=True)[:n]


class MongoMemory:
    backend = "mongodb"

    def __init__(self, person: str):
        from pymongo import MongoClient

        self.person = person
        self.col = MongoClient(MONGODB_URI, serverSelectionTimeoutMS=8000)[MONGODB_DB]["walks"]
        self.col.create_index([("person", 1), ("date", -1)], unique=True)

    def get(self, date: str):
        return self.col.find_one({"person": self.person, "date": date}, {"_id": 0})

    def save_nudge(self, date: str, nudge: str, meta: dict):
        self.col.update_one(
            {"person": self.person, "date": date},
            {"$set": {"nudge": nudge, "meta": meta, "created_at": _now()},
             "$setOnInsert": {"walk": None}},
            upsert=True,
        )

    def log_walk(self, date: str, minutes: int, felt: str, note: str):
        self.col.update_one(
            {"person": self.person, "date": date},
            {"$set": {"walk": {"minutes": minutes, "felt": felt, "note": note, "logged_at": _now()}}},
            upsert=True,
        )

    def recent(self, n: int = 5, before: str = None) -> list:
        q = {"person": self.person}
        if before:
            q["date"] = {"$lt": before}
        return list(self.col.find(q, {"_id": 0}).sort("date", -1).limit(n))


def get_memory(person: str):
    if MONGODB_URI:
        return MongoMemory(person)
    return JsonMemory(person)
