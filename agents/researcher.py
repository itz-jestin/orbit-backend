import asyncio

from utils.logger import logger
from utils.json_utils import extract_json
from tools.search import search_web_detailed
from tools.llm import llm
from state import ResearchState

# Keep prompts small: long prompts are slower and burn free-tier tokens
MAX_CONTENT_CHARS = 1000
FAILED_ANSWER = "Research failed for this question due to an internal error."


async def _search_one(index, question, resolved_entity):
    logger.info(f"Researching question {index}: {question}")
    search_query = f"{resolved_entity}: {question}" if resolved_entity else question
    try:
        # Tavily is a blocking call — run it in a thread so searches run in parallel
        data = await asyncio.to_thread(search_web_detailed, search_query)
    except Exception as e:
        logger.error(f"Search failed for question {index}: {e}")
        data = {"answer": "", "results": []}
    logger.info(f"Found {len(data['results'])} search results for question {index}")
    return data


def _format_block(index, question, search, issue):
    lines = [f"### Question {index}", question, "", "Search results:"]
    if not search["results"]:
        lines.append("(no search results were found for this question)")
    for item in search["results"]:
        content = (item.get("content") or "")[:MAX_CONTENT_CHARS]
        lines.append(
            f"- Title: {item.get('title', '')}\n"
            f"  URL: {item.get('url', '')}\n"
            f"  Content: {content}"
        )
    if issue:
        lines.append(
            f"\nA reviewer flagged this issue with the previous answer to THIS "
            f"question. Fix it in your new answer:\n{issue}"
        )
    return "\n".join(lines)


def _fallback_result(question, search):
    """Used when the LLM fails: fall back to Tavily's own summary answer
    (no extra LLM call), or mark the question as failed."""
    if search["answer"] and search["results"]:
        return {
            "question": question,
            "answer": search["answer"],
            "sources": [r["url"] for r in search["results"] if r.get("url")],
        }
    return {"question": question, "answer": FAILED_ANSWER, "sources": []}


async def researcher(state: ResearchState):
    logger.info("Researcher started")

    resolved_entity = state.get("resolved_entity", "")
    questions = state["sub_questions"]

    # Per-question reviewer feedback from a previous critic pass (if any)
    critique = state.get("critique") or {}
    issues_by_question = {
        qi["question"]: qi["issue"]
        for qi in critique.get("question_issues", [])
        if isinstance(qi, dict) and "question" in qi and "issue" in qi
    }

    # 1) All web searches in parallel (no LLM involved, fast)
    searches = await asyncio.gather(
        *[_search_one(i, q, resolved_entity) for i, q in enumerate(questions, start=1)]
    )

    # 2) ONE LLM call that answers every sub-question at once
    blocks = "\n\n".join(
        _format_block(i, q, s, issues_by_question.get(q))
        for i, (q, s) in enumerate(zip(questions, searches), start=1)
    )

    prompt = f"""
You are an AI Research Assistant.

You are researching: {resolved_entity if resolved_entity else "the topic of the questions below"}

Below are {len(questions)} questions, each followed by its OWN web search results.
Answer EACH question using ONLY the search results listed under that question.
Do not mix in information about a different person, place, or thing with a
similar name, and do not add outside knowledge.
If a question's search results do not contain the answer, say so plainly.
Keep each answer specific and concise (about 80-200 words), and include
concrete facts and figures from the results where available.

{blocks}

Return ONLY valid JSON (no markdown, no explanation) in exactly this shape,
with exactly {len(questions)} items in the same order as the questions:

{{
  "results": [
    {{"question": "exact question text", "answer": "...", "sources": ["url1", "url2"]}}
  ]
}}
"""

    logger.info(f"Sending one batched request to LLM for {len(questions)} questions")

    results = []
    try:
        response = await llm.ainvoke(prompt)
        data = extract_json(response.content)
        items = data.get("results", []) if isinstance(data, dict) else data
        if not isinstance(items, list):
            items = []

        for i, (question, search) in enumerate(zip(questions, searches)):
            item = items[i] if i < len(items) and isinstance(items[i], dict) else {}
            answer = str(item.get("answer", "")).strip()
            if answer:
                sources = [u for u in item.get("sources", []) if isinstance(u, str)]
                if not sources:
                    sources = [r["url"] for r in search["results"] if r.get("url")]
                results.append({"question": question, "answer": answer, "sources": sources})
            else:
                logger.warning(f"No answer returned for question {i + 1}; using search summary")
                results.append(_fallback_result(question, search))
    except Exception as e:
        logger.error(f"Batched research LLM call failed, using search summaries instead: {e}")
        results = [_fallback_result(q, s) for q, s in zip(questions, searches)]

    state["research_results"] = results
    logger.info(f"Researcher completed {len(results)} questions")

    return state