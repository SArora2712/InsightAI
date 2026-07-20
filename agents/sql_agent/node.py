"""
InsightAI - LangGraph node wrapper for the SQL Agent.
Follows the same pattern as the Week 1 Document RAG node: reads the question
from shared state, writes structured results back into state.
"""
from agents.sql_agent.generator import run_sql_agent

def sql_agent_node(state: dict) -> dict:
    result = run_sql_agent(state["query"])
    return {"sql_result": result}         