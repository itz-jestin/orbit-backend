from utils.logger import logger
from state import ResearchState
from tools.llm import llm
from schemas.critic import CriticResult

APPROVAL_SCORE_THRESHOLD = 85

INACCURACY_SIGNALS = (
    "inaccura", "incorrect", "error", "mistak", "wrong", "misleading",
    "not accurate", "factual issue", "false claim",
)


def _feedback_flags_inaccuracy(feedback: str) -> bool:
    lowered = feedback.lower()
    return any(signal in lowered for signal in INACCURACY_SIGNALS)


def _any_text_flags_inaccuracy(critique: dict) -> bool:
    """Scan both the overall feedback and every per-question issue for
    inaccuracy language, since the critic sometimes only names a factual
    problem inside question_issues rather than the top-level summary."""
    texts = [critique.get("feedback", "")]
    texts += [qi.get("issue", "") for qi in critique.get("question_issues", [])]
    return any(_feedback_flags_inaccuracy(t) for t in texts)


def critic(state: ResearchState):
    logger.info("Critic started")

    report = state["final_report"]
    sub_questions = state["sub_questions"]
    research = state["research_results"]

    prompt = f"""
You are a senior research reviewer. Review this report:

{report}

It was built to answer these sub-questions:
{chr(10).join(f"- {q}" for q in sub_questions)}

ORIGINAL RESEARCH it should be based on:

{research}

Evaluate and score (1-9 unless noted) on:
1. Accuracy
2. Coverage
3. Clarity
4. Structure
5. Source quality — penalize if sources are generic blogs/SEO farms/aggregators
   rather than authoritative (news outlets, .gov/.edu, journals, official sites,
   Wikipedia). Score >6 requires most cited URLs be authoritative.
6. GROUNDING (critical): Every quote, date/year, and attribution (e.g. "According
   to X", "X states that...") in the report must be traceable verbatim or
   near-verbatim to the ORIGINAL RESEARCH. Any quote, date, or attributed claim
   NOT present there is a fabrication — even if factually true elsewhere. Outside
   knowledge not present in the research is not allowed.

Any fabrication found under #6, or any other factual error, means
accuracy_issue_found MUST be true — write your feedback first, then set this
field to match what the feedback says. They must never contradict each other.

Add an entry to question_issues only for sub-questions with a specific problem
(factual error or missing depth). Leave it empty if issues are report-wide only.

Return valid JSON:
{{
    "score": 95,
    "coverage": 9,
    "clarity": 9,
    "structure": 9,
    "source_quality": 9,
    "accuracy_issue_found": false,
    "feedback": "...",
    "question_issues": [
        {{"question": "exact sub-question text", "issue": "what's wrong with the answer to this one"}}
    ]
}}
"""
    logger.info("Sending report to critic LLM")

    try:
        response = llm.with_structured_output(CriticResult).invoke(prompt)
    except Exception as e:
        logger.error(f"LLM call failed in critic: {e}")
        raise

    logger.info("Critic response received")

    critique = response.model_dump()

    if state.get("_grounding_issues"):
        logger.warning(
            "Automated grounding check found unverified claims — "
            "forcing accuracy_issue_found=True regardless of critic LLM output."
        )
        critique["accuracy_issue_found"] = True
        critique["feedback"] = (
            critique.get("feedback", "")
            + "\n\nAutomated grounding check found: "
            + "; ".join(state["_grounding_issues"])
        )

    if _any_text_flags_inaccuracy(critique):
        if not critique["accuracy_issue_found"]:
            logger.warning(
                "Critic text (feedback or a question_issue) mentions an "
                "inaccuracy but accuracy_issue_found was false — overriding "
                "to true."
            )
        critique["accuracy_issue_found"] = True

    approved = (
        critique["score"] >= APPROVAL_SCORE_THRESHOLD
        and not critique["accuracy_issue_found"]
    )
    critique["approved"] = approved

    state["critique"] = critique
    state["feedback"] = critique["feedback"]

    if approved:
        logger.info(f"Report approved with score {critique['score']}")
    else:
        logger.warning("Report rejected. Incrementing retry count.")
        state["retries"] += 1
        if state["retries"] >= 2:
            logger.warning("Max retries reached — forcing approval bypass to stop the loop.")
            critique["force_stop"] = True

    logger.info("Critic completed")

    return state