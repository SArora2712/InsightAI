"""
InsightAI - LangGraph node wrapper for the Web Search Agent.
Same shape as the SQL and RAG agent nodes: reads `question` from shared
state, writes structured results back into state.
"""
import sys
from pathlib import Path



from core.search_client import search_web
from agents.web_agent.synthesizer import synthesize_answer


def run_web_agent(question: str) -> dict:
    search_result = search_web(question)
    if search_result["error"]:
        return {"question": question, "answer": None, "sources": [], "error": search_result["error"]}
    answer = synthesize_answer(question, search_result["results"])
    sources = [{"title": r["title"], "url": r["url"], "snippet": r["content"][:300]} for r in search_result["results"]]
    return {"question": question, "answer": answer, "sources": sources, "error": None}


def web_agent_node(state: dict) -> dict:
    result = run_web_agent(state["query"])
    return {"web_result": result}          