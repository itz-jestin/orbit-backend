import os
import re

from utils.logger import logger
from utils.json_utils import extract_json
from state import ResearchState
from prompts.planner_prompt import PLANNER_PROMPT
from schemas.planner import PlannerOutput
from tools.llm import llm

PLACEHOLDER_PATTERN = re.compile(r"\[[a-zA-Z0-9 _-]+\]")

# Fewer sub-questions = smaller prompts and faster runs. Change on Render if needed.
MAX_SUB_QUESTIONS = int(os.getenv("MAX_SUB_QUESTIONS", "3"))


def _fallback_plan(query: str) -> PlannerOutput:
    """If the model's reply can't be used, research the original query directly."""
    return PlannerOutput(ambiguous=False, resolved_entity=query, sub_questions=[query])


def planner(state: ResearchState):
    logger.info("Planner started")

    query = state["query"]

    prompt = f"""
{PLANNER_PROMPT}

User Query:
{query}
"""

    try:
        response = llm.invoke(prompt)
        logger.info("Raw planner response received")
        data = extract_json(response.content)
        validated = PlannerOutput(**data)
    except Exception as e:
        logger.warning(f"Planner output unusable ({e}); researching the original query directly")
        validated = _fallback_plan(query)

    if validated.ambiguous:
        logger.info(
            f"Query '{query}' treated as ambiguous; "
            f"planner resolved to: {validated.resolved_entity}"
        )

    # Defensive check: drop any unfilled template placeholder
    broken = [q for q in validated.sub_questions if PLACEHOLDER_PATTERN.search(q)]
    if broken:
        logger.warning(f"Planner produced unfilled placeholders, dropping: {broken}")
        validated.sub_questions = [q for q in validated.sub_questions if q not in broken]

    sub_questions = validated.sub_questions[:MAX_SUB_QUESTIONS] or [query]

    state["sub_questions"] = sub_questions
    state["resolved_entity"] = validated.resolved_entity or query

    logger.info(f"Planner generated {len(sub_questions)} sub-questions")
    logger.info("Planner completed")

    return state