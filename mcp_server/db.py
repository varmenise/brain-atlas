"""JSONL helpers for the session log."""

import json
import os
from pathlib import Path

SESSIONS_FILE = Path(__file__).parent / "data" / "sessions.jsonl"


def append_session(record: dict) -> None:
    """Append one session record to sessions.jsonl (created if absent)."""
    os.makedirs(SESSIONS_FILE.parent, exist_ok=True)
    with open(SESSIONS_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(record) + "\n")


def read_sessions() -> list[dict]:
    """Return all session records from sessions.jsonl, or [] if file doesn't exist."""
    if not SESSIONS_FILE.exists():
        return []
    records = []
    with open(SESSIONS_FILE, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                records.append(json.loads(line))
    return records
