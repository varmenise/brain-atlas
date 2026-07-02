"""Evaluator agent — scores interview answers and extracts knowledge gaps.

Tools:
  score_answer(question, answer, key_concepts) -> EvaluationResult
  extract_gaps(key_concepts, covered_concepts)  -> list[str]

The agent calls score_answer after each answer. extract_gaps is deterministic
(no LLM) — missed key_concepts become gap tags directly (DECISIONS.md D4).
"""

import sys
from pathlib import Path
from typing import Optional

from google.adk.agents import Agent
from pydantic import BaseModel, Field

# Allow importing from mcp_server without installing it as a package
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "mcp_server"))
from server import get_evaluation_rubric  # noqa: E402

# ---------------------------------------------------------------------------
# Structured output schema
# ---------------------------------------------------------------------------


class DimensionScore(BaseModel):
    dimension: str = Field(description="Rubric dimension name")
    score: float = Field(description="Score 0-10 for this dimension")
    covered_concepts: list[str] = Field(
        description="key_concepts the candidate clearly addressed"
    )
    missed_concepts: list[str] = Field(
        description="key_concepts the candidate missed or only partially addressed"
    )
    reasoning: str = Field(description="One-sentence justification for the score")


class EvaluationResult(BaseModel):
    dimension_scores: list[DimensionScore]
    overall_score: float = Field(description="Weighted average score 0-10")
    summary: str = Field(description="2-3 sentence overall assessment")
    gaps: list[str] = Field(description="List of gap tags the candidate missed")


class EvaluatorInput(BaseModel):
    question_text: str = Field(description="The interview question that was asked")
    answer_text: str = Field(description="The candidate's answer")
    question_type: str = Field(description="The type of question, e.g. system_design")
    key_concepts: list[str] = Field(description="List of expected gap tags")


# ---------------------------------------------------------------------------
# Tools
# ---------------------------------------------------------------------------


def get_rubric(question_type: str) -> dict:
    """Fetch the evaluation rubric for the given question type from the MCP server.

    Args:
        question_type: e.g. "system_design"

    Returns:
        The rubric JSON containing dimensions and weights.
    """
    rubric = get_evaluation_rubric(question_type)
    if not rubric:
        return {"error": f"No rubric found for question type '{question_type}'."}

    return rubric


def extract_gaps(
    key_concepts: list[str],
    covered_concepts: list[str],
) -> list[str]:
    """Return gap tags for concepts the candidate missed (deterministic, no LLM).

    Args:
        key_concepts: All expected concepts for the question.
        covered_concepts: Concepts the Evaluator marked as addressed.

    Returns:
        List of missed gap tags (snake_case strings).
    """
    covered_set = set(covered_concepts)
    return [c for c in key_concepts if c not in covered_set]


# ---------------------------------------------------------------------------
# Agent definition
# ---------------------------------------------------------------------------

evaluator_agent = Agent(
    name="evaluator_agent",
    model="gemini-flash-lite-latest",
    mode="task",
    input_schema=EvaluatorInput,
    output_schema=EvaluationResult,
    description="Evaluates technical interview answers and extracts knowledge gaps.",
    instruction="""You are an expert technical interviewer evaluating a candidate's answer.

You will receive your inputs as a structured task (question_text, answer_text, question_type, key_concepts).

Your job:
1. Call get_rubric with the provided question_type to get the scoring dimensions and weights.
2. Score each rubric dimension from 0 to 10.
3. For each dimension, list which key_concepts the candidate covered and which they missed.
4. Compute the overall_score as the weighted average (use the weights provided).
5. Call extract_gaps with the expected key_concepts and the concepts you marked as covered.
6. Write a 2-3 sentence summary of the answer quality.
7. Call finish_task with your final EvaluationResult, including the gaps returned by extract_gaps.

Be strict but fair. A score of 7+ means the candidate addressed the concept clearly.
A score below 5 means significant gaps exist. Score 0 if not mentioned at all.
""",
    tools=[get_rubric, extract_gaps],
)
