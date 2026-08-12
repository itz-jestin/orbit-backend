import asyncio

from utils.logger import logger
from tools.search import search_web
from tools.llm import llm
from schemas.researcher import ResearchResult
from state import ResearchState


async def _research_one(index, question, resolved_entity, issues_by_question):
    logger.info(f"Researching question {index}: {question}")

    search_query = f"{resolved_entity}: {question}" if resolved_entity else question

    try:
        # search_web is likely synchronous/blocking — run it in a thread
        # so it doesn't block the event loop while other questions run.
        search_results = await asyncio.to_thread(search_web, search_query)
    except Exception as e:
        logger.error(f"Search failed for question {index}: {e}")
        search_results = []

    logger.info(f"Found {len(search_results)} search results")

    context = ""
    for item in search_results:
        context += f"""
Title:
{item['title']}

Content:
{item['content']}

URL:
{item['url']}

"""

    specific_issue = issues_by_question.get(question)
    feedback_text = ""
    if specific_issue:
        feedback_text = f"""
A reviewer flagged this specific issue with your previous answer to
THIS question:

{specific_issue}

Fix this issue in your new answer.
"""

    prompt = f"""
You are an AI Research Assistant.

You are researching: {resolved_entity if resolved_entity else "the topic in the question below"}

Answer ONLY using the search results below. Do not mix in information
about a different person, place, or thing with a similar name.

Question:
{question}

Search Results:

{context}

{feedback_text}

Return ONLY valid JSON.

{{
    "question": "...",
    "answer": "...",
    "sources": ["url1","url2"]
}}
"""

    logger.info(f"Sending request to LLM for question {index}")

    try:
        response = await llm.with_structured_output(ResearchResult).ainvoke(prompt)
    except Exception as e:
        logger.error(f"LLM call failed for question {index}: {e}")
        response = ResearchResult(
            question=question,
            answer="Research failed for this question due to an internal error.",
            sources=[],
        )

    logger.info(f"Completed question {index}")
    return response.model_dump()


async def researcher(state: ResearchState):
    logger.info("Researcher started")

    resolved_entity = state.get("resolved_entity", "")

    # Build a lookup of question -> specific issue, from the critic's
    # last pass. Only questions with a matching entry get feedback
    # injected; everything else is treated as fine.
    critique = state.get("critique") or {}
    question_issues = critique.get("question_issues", [])
    issues_by_question = {qi["question"]: qi["issue"] for qi in question_issues}

    tasks = [
        _research_one(index, question, resolved_entity, issues_by_question)
        for index, question in enumerate(state["sub_questions"], start=1)
    ]

    results = await asyncio.gather(*tasks)

    state["research_results"] = list(results)
    logger.info(f"Researcher completed {len(results)} questions")

    return state