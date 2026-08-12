from langgraph.graph import StateGraph, END

from state import ResearchState
from agents.planner import planner
from agents.researcher import researcher
from agents.writer import writer
from agents.critic import critic
from tools.verify import find_ungrounded_claims
from utils.logger import logger


def should_retry(state):
    critique = state["critique"]
    retries = state["retries"]

    print("Retries:", retries)
    print("Approved:", critique["approved"])

    if critique["approved"]:
        has_feedback = bool(critique.get("feedback")) or bool(critique.get("question_issues"))
        if has_feedback and not state.get("revised", False):
            return "revise"
        return "done"

    if critique.get("force_stop") or retries >= 1:
        return "done"

    return "retry"


def grounding_check(state: ResearchState):
    issues = find_ungrounded_claims(state["final_report"], state["research_results"])
    if issues:
        logger.warning(f"Grounding check failed: {issues}")
        # Force critic to see this regardless of what its own prompt catches
        state["_grounding_issues"] = issues
    else:
        state["_grounding_issues"] = []
    return state


builder = StateGraph(ResearchState)

builder.add_node("planner", planner)
builder.add_node("researcher", researcher)
builder.add_node("writer", writer)
builder.add_node("grounding_check", grounding_check)
builder.add_node("critic", critic)

builder.set_entry_point("planner")

builder.add_edge("planner", "researcher")
builder.add_edge("researcher", "writer")
builder.add_edge("writer", "grounding_check")
builder.add_edge("grounding_check", "critic")

builder.add_conditional_edges(
    "critic",
    should_retry,
    {   "done": END,
        "retry": "researcher",
        "revise": "writer",
    },
)

graph = builder.compile()