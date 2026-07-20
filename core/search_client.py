"""
InsightAI - Web search client wrapper (Tavily).
Same graceful-fallback pattern as llm_client.py: works without a key by
returning an empty, clearly-labeled result rather than crashing the pipeline.
"""
import os

DEFAULT_MAX_RESULTS = 5


def search_web(query: str, max_results: int = DEFAULT_MAX_RESULTS) -> dict:
    """
    Search the web via Tavily. Returns a normalized dict:
    {
        "query": str,
        "results": [{"title": str, "url": str, "content": str, "score": float}, ...],
        "tavily_answer": str | None,   # Tavily's own quick AI summary, if available
        "error": str | None,
    }
    """
    api_key = os.getenv("TAVILY_API_KEY", "")
    if not api_key:
        return {
            "query": query,
            "results": [],
            "tavily_answer": None,
            "error": "No TAVILY_API_KEY set — skipping web search. Add your key to .env.",
        }

    try:
        from tavily import TavilyClient
        client = TavilyClient(api_key=api_key)
        response = client.search(
            query=query,
            search_depth="basic",       # "advanced" costs 2 credits vs 1 - stay cheap by default
            max_results=max_results,
            include_answer=True,        # Tavily's own synthesized answer, useful as a cross-check
        )
    except Exception as e:
        return {
            "query": query,
            "results": [],
            "tavily_answer": None,
            "error": f"Tavily search failed: {e}",
        }

    normalized_results = [
        {
            "title": r.get("title", ""),
            "url": r.get("url", ""),
            "content": r.get("content", ""),
            "score": r.get("score", 0.0),
        }
        for r in response.get("results", [])
    ]

    return {
        "query": query,
        "results": normalized_results,
        "tavily_answer": response.get("answer"),
        "error": None,
    }