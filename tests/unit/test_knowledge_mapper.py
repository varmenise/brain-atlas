"""Unit tests for the Knowledge Mapper tools.

All tools are deterministic — no LLM mocking needed.
db.read_sessions is monkeypatched to control session history.
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "mcp_server"))

import db
from app.knowledge_mapper.mapper import build_gap_graph, build_study_plan, get_resources

# ---------------------------------------------------------------------------
# T4.2 — build_gap_graph
# ---------------------------------------------------------------------------


def test_build_gap_graph_returns_correct_node_count(monkeypatch):
    monkeypatch.setattr(db, "read_sessions", lambda: [])

    gaps = ["geospatial_indexing", "cap_theorem", "thundering_herd"]
    graph = build_gap_graph(gaps=gaps, session_id="s001")

    assert len(graph["nodes"]) == 3
    node_ids = {n["data"]["id"] for n in graph["nodes"]}
    assert node_ids == set(gaps)


def test_build_gap_graph_node_size_reflects_frequency(monkeypatch):
    """geospatial_indexing appeared in 2 past sessions → size should be 2."""
    monkeypatch.setattr(
        db,
        "read_sessions",
        lambda: [
            {"session_id": "s001", "gaps": ["geospatial_indexing", "cap_theorem"]},
            {"session_id": "s002", "gaps": ["geospatial_indexing", "thundering_herd"]},
        ],
    )

    graph = build_gap_graph(
        gaps=["geospatial_indexing", "cap_theorem"],
        session_id="s003",
    )

    nodes_by_id = {n["data"]["id"]: n["data"] for n in graph["nodes"]}
    assert nodes_by_id["geospatial_indexing"]["size"] == 2  # severity(1) × frequency(2)
    assert nodes_by_id["cap_theorem"]["size"] == 1          # appeared in 1 session


def test_build_gap_graph_creates_edges_for_co_occurring_gaps(monkeypatch):
    monkeypatch.setattr(
        db,
        "read_sessions",
        lambda: [
            {"session_id": "s001", "gaps": ["cap_theorem", "database_sharding"]},
        ],
    )

    graph = build_gap_graph(
        gaps=["cap_theorem", "database_sharding"],
        session_id="s002",
    )

    assert len(graph["edges"]) == 1
    edge = graph["edges"][0]["data"]
    assert edge["source"] in {"cap_theorem", "database_sharding"}
    assert edge["target"] in {"cap_theorem", "database_sharding"}
    assert edge["weight"] == 1


def test_build_gap_graph_edge_weight_reflects_co_occurrence_count(monkeypatch):
    """Two tags co-occurring in 3 sessions → edge weight should be 3."""
    monkeypatch.setattr(
        db,
        "read_sessions",
        lambda: [
            {"session_id": "s001", "gaps": ["cap_theorem", "database_sharding"]},
            {"session_id": "s002", "gaps": ["cap_theorem", "database_sharding"]},
            {"session_id": "s003", "gaps": ["cap_theorem", "database_sharding"]},
        ],
    )

    graph = build_gap_graph(
        gaps=["cap_theorem", "database_sharding"],
        session_id="s004",
    )

    assert graph["edges"][0]["data"]["weight"] == 3


def test_build_gap_graph_valid_cytoscape_structure(monkeypatch):
    monkeypatch.setattr(db, "read_sessions", lambda: [])

    graph = build_gap_graph(gaps=["cap_theorem"], session_id="s001")

    assert "nodes" in graph
    assert "edges" in graph
    node = graph["nodes"][0]["data"]
    assert "id" in node
    assert "label" in node
    assert "size" in node
    assert "domain" in node
    assert "resolved" in node


# ---------------------------------------------------------------------------
# T4.3 — get_resources
# ---------------------------------------------------------------------------


def test_get_resources_returns_resources_for_known_tags():
    result = get_resources(["geospatial_indexing", "cap_theorem"])
    assert "geospatial_indexing" in result
    assert "cap_theorem" in result
    assert len(result["geospatial_indexing"]) >= 1
    assert len(result["cap_theorem"]) >= 1


def test_get_resources_returns_empty_list_for_unknown_tag():
    result = get_resources(["completely_unknown_tag"])
    assert result["completely_unknown_tag"] == []


# ---------------------------------------------------------------------------
# T4.4 — build_study_plan
# ---------------------------------------------------------------------------


def test_build_study_plan_contains_gap_labels(monkeypatch):
    monkeypatch.setattr(db, "read_sessions", lambda: [])

    gaps = ["cap_theorem", "thundering_herd"]
    graph = build_gap_graph(gaps=gaps, session_id="s001")
    resources = get_resources(gaps)
    plan = build_study_plan(graph=graph, resources=resources)

    assert "Cap Theorem" in plan
    assert "Thundering Herd" in plan


def test_build_study_plan_orders_by_priority_descending(monkeypatch):
    """The gap with higher frequency should appear first in the study plan."""
    monkeypatch.setattr(
        db,
        "read_sessions",
        lambda: [
            {"session_id": "s001", "gaps": ["cap_theorem"]},
            {"session_id": "s002", "gaps": ["cap_theorem"]},
        ],
    )

    gaps = ["thundering_herd", "cap_theorem"]  # cap_theorem has higher frequency
    graph = build_gap_graph(gaps=gaps, session_id="s003")
    resources = get_resources(gaps)
    plan = build_study_plan(graph=graph, resources=resources)

    cap_pos = plan.index("Cap Theorem")
    thunder_pos = plan.index("Thundering Herd")
    assert cap_pos < thunder_pos  # cap_theorem should appear first
