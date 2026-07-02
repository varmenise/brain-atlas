"""BrainAtlas MCP server — knowledge and persistence layer for all agents."""

import json
import re
from datetime import datetime, timezone
from pathlib import Path

from fastmcp import FastMCP

from db import append_session

# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------

DATA_DIR = Path(__file__).parent / "data"


def _load(filename: str) -> any:
    with open(DATA_DIR / filename, "r", encoding="utf-8") as f:
        return json.load(f)


QUESTIONS: list[dict] = _load("questions.json")
RUBRICS: dict = _load("rubrics.json")
RESOURCES: dict = _load("resources.json")

# ---------------------------------------------------------------------------
# Security helper
# ---------------------------------------------------------------------------

MAX_INPUT_LENGTH = 8000  # characters


def sanitize_input(text: str) -> str:
    """Strip control characters and truncate to prevent prompt injection."""
    # Remove control characters except newline and tab
    text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", text)
    return text[:MAX_INPUT_LENGTH]


# ---------------------------------------------------------------------------
# MCP server
# ---------------------------------------------------------------------------

mcp = FastMCP("brain-atlas")


@mcp.tool()
def get_interview_questions(
    role: str,
    domains: list[str],
    difficulty: int,
    count: int,
) -> list[dict]:
    """Return interview questions matching role, domains, and difficulty.

    Returns all available questions if fewer exist than count (no error).
    """
    results = [
        q for q in QUESTIONS
        if q["role"] == role
        and q["domain"] in domains
        and q["difficulty"] <= difficulty
    ]
    return results[:count]


@mcp.tool()
def get_evaluation_rubric(question_type: str) -> dict:
    """Return the rubric for a question type, including dimensions and weights.

    Returns an empty dict for unknown question types (no error).
    """
    return RUBRICS.get(question_type, {})


@mcp.tool()
def get_study_resources(gap_tags: list[str]) -> dict[str, list[dict]]:
    """Return curated study resources for each gap tag.

    Unknown gap tags return an empty list (no error).
    """
    return {tag: RESOURCES.get(tag, []) for tag in gap_tags}


@mcp.tool()
def log_session_result(
    session_id: str,
    role: str,
    scores: dict[str, int],
    gaps: list[str],
) -> dict:
    """Append a completed session record to sessions.jsonl.

    No deduplication — same session_id logged twice produces two records.
    """
    # Sanitize any free-text fields before persisting
    safe_session_id = sanitize_input(session_id)
    safe_role = sanitize_input(role)
    safe_gaps = [sanitize_input(g) for g in gaps]

    record = {
        "session_id": safe_session_id,
        "role": safe_role,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "scores": scores,
        "gaps": safe_gaps,
    }
    append_session(record)
    return {"ok": True}


if __name__ == "__main__":
    mcp.run()
