"""Knowledge Mapper agent — builds a gap graph and study plan from session gaps.

Tools:
  build_gap_graph(gaps, session_id) -> dict   Cytoscape.js-compatible JSON
  get_resources(gap_tags)           -> dict   {tag: [resources]}
  build_study_plan(graph, resources) -> str   Markdown study plan

All tools are deterministic — no LLM calls. The agent runs once at session end.
"""

import sys
from itertools import combinations
from pathlib import Path



sys.path.insert(0, str(Path(__file__).parent.parent.parent / "mcp_server"))

import db  # noqa: E402
from server import get_study_resources  # noqa: E402

# ---------------------------------------------------------------------------
# Tools
# ---------------------------------------------------------------------------


def build_gap_graph(gaps: list[str], session_id: str) -> dict:
    """Build a Cytoscape.js-compatible graph from the session's gap tags.

    Reads sessions.jsonl to compute cross-session frequency and co-occurrence.
    Node size = severity (fixed 1) × frequency across sessions.
    Edge weight = number of sessions where two tags co-occurred.

    Args:
        gaps: Gap tags collected from the current session.
        session_id: ID of the current session (already logged in sessions.jsonl).

    Returns:
        {"nodes": [...], "edges": [...]} in Cytoscape.js element format.
    """
    all_sessions = db.read_sessions()

    # Compute frequency and co-occurrence across all logged sessions
    frequency: dict[str, int] = {}
    co_occurrence: dict[tuple, int] = {}

    for session in all_sessions:
        session_gaps = session.get("gaps", [])
        for tag in session_gaps:
            frequency[tag] = frequency.get(tag, 0) + 1
        for tag1, tag2 in combinations(sorted(session_gaps), 2):
            key = (tag1, tag2)
            co_occurrence[key] = co_occurrence.get(key, 0) + 1

    # Ensure current session gaps have at least frequency 1 if not yet logged
    for tag in gaps:
        if tag not in frequency:
            frequency[tag] = 1

    severity = 1  # Fixed for prototype — DECISIONS.md D5

    nodes = []
    edges = []

    # Map ALL gaps from ALL sessions (Global Atlas View)
    for tag in frequency.keys():
        size = severity * frequency.get(tag, 1)
        nodes.append({
            "data": {
                "id": tag,
                "label": tag.replace("_", " ").title(),
                "size": size,
                "domain": "system_design",
                "resolved": False
            }
        })

    # Map edges between ALL gaps that have co-occurred
    for (tag1, tag2), weight in co_occurrence.items():
        edges.append({
            "data": {
                "id": f"{tag1}--{tag2}",
                "source": tag1,
                "target": tag2,
                "weight": weight
            }
        })

    return {"nodes": nodes, "edges": edges}


def get_resources(gap_tags: list[str]) -> dict:
    """Fetch curated study resources for each gap tag from the MCP server.

    Args:
        gap_tags: List of gap tag strings from the current session.

    Returns:
        {tag: [resource dicts]} — empty list for unknown tags.
    """
    return get_study_resources(gap_tags)


def build_study_plan(graph: dict, resources: dict) -> str:
    """Format a markdown study plan from the graph nodes and their resources.

    Nodes are sorted by size descending (biggest gap first).

    Args:
        graph: Output of build_gap_graph.
        resources: Output of get_resources.

    Returns:
        Markdown string with one section per gap tag.
    """
    nodes = sorted(graph.get("nodes", []), key=lambda n: n["data"]["size"], reverse=True)

    lines = ["# Study Plan\n", "Gaps are ordered by priority (most frequent first).\n"]

    for node in nodes:
        tag = node["data"]["id"]
        label = node["data"]["label"]
        size = node["data"]["size"]
        tag_resources = resources.get(tag, [])

        lines.append(f"## {label}  _(priority: {size})_\n")
        if tag_resources:
            for r in tag_resources:
                lines.append(f"- [{r['title']}]({r['url']}) — {r['type']}")
        else:
            lines.append("- No resources found yet.")
        lines.append("")

    return "\n".join(lines)


