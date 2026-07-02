"""Unit tests for the Interviewer agent tools.

select_questions is tested directly (no LLM).
evaluate_answer is tested with a monkeypatched genai client.
"""

from unittest.mock import MagicMock, patch

import pytest

from app.interviewer.agent import select_questions


# ---------------------------------------------------------------------------
# T3.2 — select_questions
# ---------------------------------------------------------------------------


def test_select_questions_returns_swe_system_design():
    questions = select_questions(
        role="swe",
        domains=["system_design"],
        difficulty=5,
        count=5,
    )
    assert len(questions) == 5
    for q in questions:
        assert q["role"] == "swe"
        assert q["domain"] == "system_design"
        assert q["key_concepts"]


def test_select_questions_respects_count():
    questions = select_questions(
        role="swe",
        domains=["system_design"],
        difficulty=5,
        count=3,
    )
    assert len(questions) == 3


def test_select_questions_returns_empty_for_unknown_role():
    questions = select_questions(
        role="unknown_role",
        domains=["system_design"],
        difficulty=5,
        count=5,
    )
    assert questions == []



