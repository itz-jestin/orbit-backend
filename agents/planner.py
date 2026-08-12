import json
import re

from utils.logger import logger
from state import ResearchState
from prompts.planner_prompt import PLANNER_PROMPT
from schemas.planner import PlannerOutput
from tools.llm import llm

PLACEHOLDER_PATTERN = re.compile(r"\[[a-zA-Z0-9 _-]+\]")


def planner(state: ResearchState):
    logger.info("Planner started")

    query = state["query"]

    prompt = f"""
{PLANNER_PROMPT}

User Query:
{query}
"""

    response = llm.invoke(prompt)

    content = response.content.strip()

    logger.info("Raw planner response received")

    if content.startswith("```"):
        content = content.replace("```json", "").replace("```", "").strip()

    data = json.loads(content)

    validated = PlannerOutput(**data)

    if validated.ambiguous:
        logger.info(
            f"Query '{query}' treated as ambiguous; "
            f"planner resolved to: {validated.resolved_entity}"
        )

    # Defensive check: even with the updated prompt, catch any unfilled
    # template placeholder before it reaches the researcher.
    broken = [q for q in validated.sub_questions if PLACEHOLDER_PATTERN.search(q)]
    if broken:
        logger.warning(f"Planner produced unfilled placeholders, dropping: {broken}")
        validated.sub_questions = [
            q for q in validated.sub_questions if q not in broken
        ]

    if not validated.sub_questions:
        raise ValueError(
            f"Planner produced no usable sub-questions for query: {query!r}"
        )

    state["sub_questions"] = validated.sub_questions
    state["resolved_entity"] = validated.resolved_entity

    logger.info(f"Planner generated {len(validated.sub_questions)} sub-questions")
    logger.info("Planner completed")

    return state