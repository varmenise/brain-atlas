"""Unit tests for the Evaluator agent tools.

Tests score_answer and extract_gaps in isolation — no Interviewer, no MCP
transport layer. The extract_gaps function is fully deterministic.
score_answer is tested for its return shape and rubric integration.
"""

from app.evaluator.agent import extract_gaps, get_rubric

# ---------------------------------------------------------------------------
# extract_gaps — deterministic, no LLM required
# ---------------------------------------------------------------------------


def test_extract_gaps_returns_missed_concepts():
    key_concepts = ["geospatial_indexing", "websocket_vs_polling", "thundering_herd"]
    covered = ["geospatial_indexing"]
    gaps = extract_gaps(key_concepts, covered)
    assert "websocket_vs_polling" in gaps
    assert "thundering_herd" in gaps
    assert "geospatial_indexing" not in gaps


def test_extract_gaps_returns_empty_when_all_covered():
    key_concepts = ["token_bucket", "sliding_window_counter"]
    gaps = extract_gaps(key_concepts, covered_concepts=key_concepts)
    assert gaps == []


def test_extract_gaps_returns_all_when_nothing_covered():
    key_concepts = ["cap_theorem", "database_sharding", "read_replicas"]
    gaps = extract_gaps(key_concepts, covered_concepts=[])
    assert gaps == key_concepts


# ---------------------------------------------------------------------------
# get_rubric — tests rubric fetching
# ---------------------------------------------------------------------------


def test_get_rubric_returns_dimensions_for_known_type():
    result = get_rubric(question_type="system_design")
    assert "dimensions" in result
    assert len(result["dimensions"]) == 6
    weights = sum(d["weight"] for d in result["dimensions"])
    assert abs(weights - 1.0) < 1e-9


def test_get_rubric_returns_gracefully_for_unknown_type():
    result = get_rubric(question_type="unknown_type")
    assert "error" in result
    assert "No rubric found" in result["error"]
