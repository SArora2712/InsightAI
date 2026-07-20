"""
InsightAI - Agentic loop (ReAct pattern).

Unlike the Router/Workflow orchestrator (agents/orchestrator/graph.py), the
control flow here is NOT fixed in advance. The LLM itself decides, one step
at a time, which tool to call - and after seeing each tool's actual result,
decides its NEXT action: answer now, call a different tool, or retry the
same tool with a refined question. This is the "Agent" quadrant: the LLM
directs its own actions based on environmental feedback, rather than
following a pre-drawn graph.

Kept alongside (not replacing) the Workflow version - the fixed-routing
graph is faster, cheaper, and more predictable for well-understood question
types; this loop trades some of that for genuine adaptivity.
"""
import json

from pathlib import Path


from core.llm_client import call_llm_with_tools, call_llm
from agents.orchestrator.router import route_question
from agents.agentic.tools_schema import TOOLS_SCHEMA
from core.text_utils import ensure_prose
MAX_ITERATIONS = 5

AGENT_SYSTEM_PROMPT = """You are InsightAI, a business analyst assistant
specialized in Northwind Traders.

...(existing prompt content unchanged)...

Once sufficient information has been gathered, provide a concise final answer
in plain text.

Attribute information to the relevant source when appropriate.

IMPORTANT: Report only what your tools actually returned. Do NOT add your own strategic recommendations \
or business opinions unless the user's question explicitly asked for advice or a recommendation.

CRITICAL: Your final answer MUST be written as clear, natural prose sentences for a business user - \
NEVER as raw JSON, a data dump, or code-formatted output. Synthesizing facts into readable sentences \
is required; only unsolicited opinions are restricted, not natural writing.
"""



def build_agent_tools(bm25, provider, qdrant_client):
    
    from ingestion.rag_agent import retrieve, generate_answer

    def search_internal_documents(question: str) -> dict:
        chunks = retrieve(question, bm25, provider, client=qdrant_client)
        answer = generate_answer(question, chunks)
        return {"answer": answer, "retrieved_chunks": chunks}   # <- was {"answer", "chunk_count"}
    def query_sales_database(question: str) -> dict:
        from agents.sql_agent.generator import run_sql_agent
        return run_sql_agent(question)

    def search_web(question: str) -> dict:
        from agents.web_agent.node import run_web_agent
        return run_web_agent(question)

    return {
        "query_sales_database": query_sales_database,
        "search_web": search_web,
        "search_internal_documents": search_internal_documents,
    }


def run_agentic_query(question: str, tool_dispatch: dict, max_iterations: int = MAX_ITERATIONS) -> dict:
    
    agents_needed = route_question(question)
    if not agents_needed:
        return {
            "answer": (
                "I'm InsightAI, a business analyst assistant scoped to Northwind Traders' "
                "sales data, internal reports, and directly relevant market context. That "
                "question is outside what I'm able to help with here."
            ),
            "tool_calls_made": [], "iterations": 0,
        }
    messages = [{"role": "user", "content": question}]
    tool_calls_made = []

    for iteration in range(1, max_iterations + 1):
        message = call_llm_with_tools(AGENT_SYSTEM_PROMPT, messages, TOOLS_SCHEMA)

        if message is None:
            fallback_answer = call_llm(
            "You are a business analyst assistant. Answer as best you can given "
            "any information already gathered - if you have nothing, say so honestly.",
            f"Question: {question}\n\nTool results gathered so far: {json.dumps(tool_calls_made, default=str)[:4000]}",
        )
            fallback_answer = ensure_prose(fallback_answer, question)
            return {"answer": fallback_answer, "tool_calls_made": tool_calls_made, "iterations": iteration}

        if not message.tool_calls:
            final_answer = ensure_prose(message.content, question)
            return {"answer": final_answer, "tool_calls_made": tool_calls_made, "iterations": iteration}


        # The LLM wants to act - append its tool-call request to the conversation
        messages.append({
            "role": "assistant",
            "content": message.content or "",
            "tool_calls": [
                {"id": tc.id, "type": "function",
                 "function": {"name": tc.function.name, "arguments": tc.function.arguments}}
                for tc in message.tool_calls
            ],
        })

        # Execute each requested tool call, feed the ACTUAL result back as feedback
        for tc in message.tool_calls:
            fn_name = tc.function.name
            try:
                args = json.loads(tc.function.arguments)
            except json.JSONDecodeError:
                args = {}

            fn = tool_dispatch.get(fn_name)
            if fn is None:
                result = {"error": f"Unknown tool: {fn_name}"}
            else:
                try:
                    result = fn(**args)
                except Exception as e:
                    result = {"error": str(e)}

            tool_calls_made.append({"tool": fn_name, "args": args, "result": result})

            # This is the "environmental feedback" - the LLM sees this exact
            # result on its NEXT turn and decides what to do based on it
            messages.append({
                "role": "tool",
                "tool_call_id": tc.id,
                "content": json.dumps(result, default=str)[:3000],
            })

    # Safety net: exceeded max_iterations without the LLM producing a final answer
    fallback_answer = call_llm(
        "You are a business analyst assistant. Summarize what was found, based only on the tool "
        "results provided, and note that you were unable to fully resolve the question.",
        f"Question: {question}\n\nTool results gathered so far: {json.dumps(tool_calls_made, default=str)[:4000]}",
    )
    fallback_answer = ensure_prose(fallback_answer, question) 
    return {"answer": fallback_answer, "tool_calls_made": tool_calls_made, "iterations": max_iterations}