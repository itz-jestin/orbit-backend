from tavily import TavilyClient
from config import TAVILY_API_KEY

client = TavilyClient(api_key=TAVILY_API_KEY)


def search_web_detailed(query: str, max_results: int = 3):
    """Search the web and also return Tavily's short summary answer,
    which the researcher uses as a fallback if the LLM call fails."""
    response = client.search(
        query=query,
        search_depth="advanced",
        max_results=max_results,
        include_answer=True,
    )
    return {
        "answer": response.get("answer") or "",
        "results": response.get("results", []),
    }


def search_web(query: str):
    """Kept for compatibility with any other code that imports it."""
    return search_web_detailed(query, max_results=5)["results"]