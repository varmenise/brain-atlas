"""In-process smoke tests for the BrainAtlas MCP server tools.

Run from the mcp_server/ directory:
    pip install -r requirements.txt pytest
    pytest test_mcp.py -v
"""

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "mcp_server"))

import db
from server import (
    get_evaluation_rubric,
    get_interview_questions,
    get_study_resources,
    log_session_result,
)


# ---------------------------------------------------------------------------
# Fixture: redirect sessions.jsonl to a temp file for test isolation
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def tmp_sessions(tmp_path, monkeypatch):
    """Point db.SESSIONS_FILE at a temp file so tests don't pollute real data."""
    monkeypatch.setattr(db, "SESSIONS_FILE", tmp_path / "sessions.jsonl")


# ---------------------------------------------------------------------------
# Assertion 1: get_interview_questions returns 8 questions, each with
#              non-empty key_concepts
# ---------------------------------------------------------------------------


def test_get_interview_questions_returns_all_with_key_concepts():
    questions = get_interview_questions(
        role="swe",
        domains=["system_design"],
        difficulty=5,
        count=10,
    )
    assert len(questions) == 8, f"Expected 8 questions, got {len(questions)}"
    for q in questions:
        assert q["key_concepts"], f"Question {q['id']} has empty key_concepts"


# ---------------------------------------------------------------------------
# Assertion 2: get_evaluation_rubric("system_design") returns 6 dimensions
#              whose weights sum to 100%
# ---------------------------------------------------------------------------


def test_get_evaluation_rubric_system_design():
    rubric = get_evaluation_rubric("system_design")
    dimensions = rubric.get("dimensions", [])
    assert len(dimensions) == 6, f"Expected 6 dimensions, got {len(dimensions)}"
    total_weight = sum(d["weight"] for d in dimensions)
    assert abs(total_weight - 1.0) < 1e-9, f"Weights sum to {total_weight}, expected 1.0"


# ---------------------------------------------------------------------------
# Assertion 3: get_study_resources returns 2 keys, each with ≥1 resource
# ---------------------------------------------------------------------------


def test_get_study_resources_returns_resources_for_known_tags():
    result = get_study_resources(["geospatial_indexing", "cap_theorem"])
    assert set(result.keys()) == {"geospatial_indexing", "cap_theorem"}
    for tag, resources in result.items():
        assert len(resources) >= 1, f"Tag '{tag}' has no resources"


# ---------------------------------------------------------------------------
# Assertion 4: log_session_result returns {ok: True} and appends to jsonl
# ---------------------------------------------------------------------------


def test_log_session_result_returns_ok_and_writes_file():
    result = log_session_result(
        session_id="test_session_001",
        role="swe",
        scores={"q_001": 7, "q_003": 3},
        gaps=["geospatial_indexing", "base62_encoding"],
    )
    assert result == {"ok": True}
    assert db.SESSIONS_FILE.exists(), "sessions.jsonl was not created"


# ---------------------------------------------------------------------------
# Assertion 5: read_sessions returns the appended record
# ---------------------------------------------------------------------------


def test_read_sessions_returns_appended_record():
    log_session_result(
        session_id="test_session_002",
        role="swe",
        scores={"q_004": 2},
        gaps=["token_bucket", "distributed_rate_limiting"],
    )
    sessions = db.read_sessions()
    assert len(sessions) == 1
    record = sessions[0]
    assert record["session_id"] == "test_session_002"
    assert record["role"] == "swe"
    assert "timestamp" in record
    assert record["scores"] == {"q_004": 2}
    assert record["gaps"] == ["token_bucket", "distributed_rate_limiting"]
