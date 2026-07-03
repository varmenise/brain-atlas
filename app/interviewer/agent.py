"""Interviewer agent — conducts mock interviews and drives the session flow.

Tools:
  select_questions(role, domains, difficulty, count) -> list[dict]
  evaluate_answer(question_text, answer_text, question_type, key_concepts) -> dict

The agent asks one question at a time. After each answer it silently calls
evaluate_answer. If overall_score < 5 it asks one follow-up before advancing.
After all questions it returns a session summary and the full gap list.
"""

import sys
from pathlib import Path

from google.adk.agents import Agent

# Allow importing from mcp_server and evaluator without installing as packages
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "mcp_server"))
from google.adk.tools import ToolContext

from server import get_interview_questions, log_session_result  # noqa: E402
from app.evaluator.agent import evaluator_agent  # noqa: E402

# ---------------------------------------------------------------------------
# Tools
# ---------------------------------------------------------------------------


def select_questions(
    role: str,
    domains: list[str],
    difficulty: int,
    count: int,
) -> list[dict]:
    """Fetch interview questions from the MCP server question bank.

    Args:
        role: Candidate role, e.g. "swe".
        domains: List of domains, e.g. ["system_design"].
        difficulty: Maximum difficulty level (1-5).
        count: How many questions to fetch.

    Returns:
        List of question dicts with id, question_text, key_concepts, etc.
    """
    return get_interview_questions(
        role=role,
        domains=domains,
        difficulty=difficulty,
        count=count,
    )


def save_session_results(
    tool_context: ToolContext,
    role: str,
    scores: dict[str, int],
    gaps: list[str],
) -> dict:
    """Save the final session results to the database. Call this at the very end of the interview.
    
    Args:
        role: The role being interviewed (e.g., "swe")
        scores: A dictionary mapping dimension names to scores
        gaps: The complete list of gap tags collected during the interview
    """
    return log_session_result(
        session_id=tool_context.session.id,
        role=role,
        scores=scores,
        gaps=gaps,
    )



# ---------------------------------------------------------------------------
# Agent definition
# ---------------------------------------------------------------------------

interviewer_agent = Agent(
    name="interviewer_agent",
    model="gemini-flash-lite-latest",
    description=(
        "Conducts a mock technical interview, evaluates answers silently, "
        "asks follow-ups for weak answers, and returns a session gap summary."
    ),
    instruction="""You are an expert technical interviewer conducting a mock interview.

SESSION FLOW:
1. Call select_questions(role="swe", domains=["system_design"], difficulty=4, count=1)
   to load a single, comprehensive case study. Do this silently.

2. Ask the main question clearly and wait for the candidate's initial high-level answer.

3. The Deep Dive Phase (Up to 3 Follow-ups):
   a. After EVERY answer the candidate gives, call the evaluator_agent tool with the question details and their latest answer to score it.
   b. Ask a targeted follow-up question. If the evaluator returned gaps (overall_score < 5), drill down into those specific missed concepts. If they did well, probe a different dimension of system design (e.g., scale estimation, data models, or trade-offs).
   c. Wait for their answer, evaluate it silently, and repeat.
   d. Do this for a maximum of 3 follow-up questions on this single case study.

4. After the deep dive is complete (1 main question + 3 follow-ups):
   - Call save_session_results(role, scores, gaps) with the aggregated data from the entire session.
   - Summarise the session: highlight strengths and the most significant gaps.
   - Return the full list of gap tags collected across the session.

RULES:
- Never reveal scores to the candidate during the session.
- Keep follow-up questions conversational and focused on one specific dimension of the system design.
- Be professional and encouraging, not harsh.
""",
    sub_agents=[evaluator_agent],
    tools=[select_questions, save_session_results],
)
