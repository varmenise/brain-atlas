"""End-to-end pipeline smoke test — no ADK orchestrator needed.

Runs a single hardcoded question through the full stack:
  select_questions → evaluate_answer → log_session_result
  → build_gap_graph → get_resources → build_study_plan

Prints the graph JSON and study plan to stdout.

Usage:
    export GEMINI_API_KEY=your_key_here
    uv run python scripts/run_pipeline.py

If GEMINI_API_KEY is not set, a mock evaluation result is used so the
rest of the pipeline (graph building, study plan) can still be tested.
"""

import json
import os
import sys
import uuid
from pathlib import Path

# Make mcp_server and app importable
ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT / "mcp_server"))
sys.path.insert(0, str(ROOT))

from app.interviewer.agent import select_questions
from app.evaluator.agent import evaluator_agent
from app.knowledge_mapper.mapper import build_gap_graph, build_study_plan, get_resources
from server import log_session_result

# ---------------------------------------------------------------------------
# Hardcoded weak answer for the first question (for demo purposes)
# ---------------------------------------------------------------------------

WEAK_ANSWER = (
    "I would design a ride-sharing app with a SQL database and a REST API. "
    "The backend would handle matching drivers and riders. "
    "I'd use a simple table with lat/lng columns for location."
)

STRONG_ANSWER = (
    "The core challenge is real-time location at scale. I'd use geohashing or H3 "
    "for geospatial indexing so driver lookups are O(1). For real-time updates I'd "
    "use WebSockets rather than polling — polling every second doesn't scale. "
    "The matching service reads from the geo-index, not the main database. "
    "Under surge, cache misses can cause a thundering herd — I'd use probabilistic "
    "early expiration to avoid that. Location data is eventually consistent, which "
    "is acceptable — a slightly stale driver position is fine."
)

# ---------------------------------------------------------------------------
# Mock evaluation result (used when GEMINI_API_KEY is not set)
# ---------------------------------------------------------------------------

MOCK_RESULT = {
    "overall_score": 2.0,
    "gaps": [
        "geospatial_indexing",
        "websocket_vs_polling",
        "thundering_herd",
        "matching_service_isolation",
    ],
    "summary": (
        "The candidate proposed a basic SQL approach without addressing real-time "
        "location challenges. Key concepts around geospatial indexing, WebSocket "
        "trade-offs, and thundering herd were not mentioned."
    ),
    "dimension_scores": [],
}


def run(use_strong_answer: bool = False) -> None:
    api_key = os.environ.get("GEMINI_API_KEY")
    answer = STRONG_ANSWER if use_strong_answer else WEAK_ANSWER
    answer_label = "STRONG" if use_strong_answer else "WEAK"

    print(f"\n{'='*60}")
    print("BrainAtlas — Pipeline Smoke Test")
    print(f"{'='*60}\n")

    # Step 1: Select questions
    print("Step 1: Selecting questions...")
    questions = select_questions(
        role="swe", domains=["system_design"], difficulty=4, count=1
    )
    question = questions[0]
    print(f"  Question: {question['question_text']}")
    print(f"  Key concepts: {question['key_concepts']}\n")

    # Step 2: Evaluate answer
    print(f"Step 2: Evaluating {answer_label} answer...")
    print(f"  Answer: {answer[:100]}...\n")

    if api_key:
        print("  Using real Gemini LLM via ADK evaluator_agent...")
        import asyncio
        from google.adk.runners import InMemoryRunner
        from app.evaluator.agent import EvaluatorInput
        
        task_input = EvaluatorInput(
            question_text=question["question_text"],
            answer_text=answer,
            question_type=question["question_type"],
            key_concepts=question["key_concepts"],
        )
        
        runner = InMemoryRunner(agent=evaluator_agent, app_name="app")
        # In ADK, task input can be passed as JSON string
        response = asyncio.run(runner.run(task_input.model_dump_json()))
        evaluation = response.output
    else:
        print("  ⚠️  GEMINI_API_KEY not set — using mock evaluation result.")
        evaluation = MOCK_RESULT

    print(f"  Overall score: {evaluation['overall_score']}/10")
    print(f"  Gaps: {evaluation['gaps']}")
    print(f"  Summary: {evaluation['summary']}\n")

    # Step 3: Log session
    print("Step 3: Logging session to sessions.jsonl...")
    session_id = str(uuid.uuid4())
    log_session_result(
        session_id=session_id,
        role="swe",
        scores={question["id"]: evaluation["overall_score"]},
        gaps=evaluation["gaps"],
    )
    print(f"  Session {session_id} logged.\n")

    # Step 4: Build gap graph
    print("Step 4: Building gap graph...")
    graph = build_gap_graph(gaps=evaluation["gaps"], session_id=session_id)
    print(f"  Nodes: {len(graph['nodes'])}, Edges: {len(graph['edges'])}")
    print(f"\n  Graph JSON:\n{json.dumps(graph, indent=2)}\n")

    # Step 5: Get resources
    print("Step 5: Fetching study resources...")
    resources = get_resources(evaluation["gaps"])
    total = sum(len(v) for v in resources.values())
    print(f"  {total} resources fetched across {len(resources)} gap tags.\n")

    # Step 6: Build study plan
    print("Step 6: Building study plan...")
    plan = build_study_plan(graph=graph, resources=resources)
    print(f"\n{plan}")

    print(f"{'='*60}")
    print("✅ Pipeline complete.")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    strong = "--strong" in sys.argv
    run(use_strong_answer=strong)
