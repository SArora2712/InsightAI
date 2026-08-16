"""
InsightAI - Agent v2 loop, re-expressed as a LangGraph StateGraph.

Same behavior as agents/agentic/loop.py's run_agentic_query, restructured
as explicit graph nodes instead of a manual Python loop. The out-of-scope
pre-check stays outside the graph as a wrapper, since it's a one-shot
early return, not part of the iterative tool-calling behavior.
"""
import json
from typing import TypedDict, Optional

from langgraph.graph import StateGraph, END

from core.llm_client import call_llm_with_tools, call_llm, llm_tracker
from agents.orchestrator.router import route_question
from agents.agentic.tools_schema import TOOLS_SCHEMA
from core.text_utils import ensure_prose

MAX_ITERATIONS = 5

AGENT_SYSTEM_PROMPT = """You are InsightAI, a business analyst assistant
specialized in Northwind Traders.

Once sufficient information has been gathered, provide a concise final answer
in plain text.

Attribute information to the relevant source when appropriate.

IMPORTANT: Report only what your tools actually returned. Do NOT add your own strategic recommendations \
or business opinions unless the user's question explicitly asked for advice or a recommendation.

CRITICAL: Your final answer MUST be written as clear, natural prose sentences for a business user - \
NEVER as raw JSON, a data dump, or code-formatted output. Synthesizing facts into readable sentences \
is required; only unsolicited opinions are restricted, not natural writing.

FORMATTING RULE: Write every number and figure as plain text. NEVER wrap any number, dollar amount, \
or metric in backticks, asterisks, or any other code/emphasis formatting - for example write \
"28.86" not "`28.86`" or "*28.86*". No markdown at all.

CRITICAL: Never state a specific number, metric, category, or business term unless it appears verbatim \
or is directly computed from a tool result you actually received in this conversation. If a tool \
returned an error, an empty result, or nothing relevant to part of the question, say so plainly for \
that part rather than filling the gap with a plausible-sounding number from general business knowledge."""


class AgentV2State(TypedDict):
    question: str
    messages: list[dict]
    tool_calls_made: list[dict]
    iteration: int
    final_answer: Optional[str]
    stopped_reason: Optional[str]   
    pending_tool_calls: Optional[list]


def build_agent_graph(tool_dispatch: dict,max_iterations:int= MAX_ITERATIONS):

    def agent_node(state: AgentV2State) -> AgentV2State:
        if state["iteration"] >= max_iterations:
            return {"stopped_reason": "capped"}

        iteration = state["iteration"] + 1
        choice = "required" if iteration == 1 else "auto"

        message = call_llm_with_tools(
            AGENT_SYSTEM_PROMPT, state["messages"], TOOLS_SCHEMA, tool_choice=choice
        )

        if message is None:
            return {"iteration": iteration, "stopped_reason": "call_failed"}

        new_messages = list(state["messages"])
        if message.tool_calls:
            new_messages.append({
                "role": "assistant",
                "content": message.content or "",
                "tool_calls": [
                    {"id": tc.id, "type": "function",
                     "function": {"name": tc.function.name, "arguments": tc.function.arguments}}
                    for tc in message.tool_calls
                ],
            })
            return {
                "messages": new_messages,
                "iteration": iteration,
                "pending_tool_calls": message.tool_calls,   # transient, not in TypedDict, see note below
            }
        else:
            return {
                "iteration": iteration,
                "final_answer": message.content,
                "stopped_reason": "completed",
                "pending_tool_calls":None
            }

    def tools_node(state: AgentV2State) -> AgentV2State:
        pending = state.get("pending_tool_calls") or []
        new_messages = list(state["messages"])
        new_tool_calls_made = list(state["tool_calls_made"])

        for tc in pending:
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

            new_tool_calls_made.append({"tool": fn_name, "args": args, "result": result})
            new_messages.append({

                "role": "tool",
                "tool_call_id": tc.id,
                "content": json.dumps(result, default=str)[:3000],
            })

        return {"messages": new_messages, "tool_calls_made": new_tool_calls_made,"pending_tool_calls":None}

    def finalize_node(state: AgentV2State) -> AgentV2State:
        return {"final_answer": ensure_prose(state["final_answer"], state["question"])}

    def finalize_fallback_node(state: AgentV2State) -> AgentV2State:
        reason = state.get("stopped_reason", "capped")
        if reason == "call_failed":
            prompt_prefix = "You are a business analyst assistant. Answer as best you can given any information already gathered - if you have nothing, say so honestly."
        else:
            prompt_prefix = "You are a business analyst assistant. Summarize what was found, based only on the tool results provided, and note that you were unable to fully resolve the question."

        fallback = call_llm(
            prompt_prefix,
            f"Question: {state['question']}\n\nTool results gathered so far: "
            f"{json.dumps(state['tool_calls_made'], default=str)[:4000]}",
        )
        return {"final_answer": ensure_prose(fallback, state["question"])}

    def route_after_agent(state: AgentV2State) -> str:
        if state.get("stopped_reason") in ("call_failed","capped"):
            return "finalize_fallback"
        if state.get("final_answer") is not None:
            return "finalize"

        return "tools"

    graph = StateGraph(AgentV2State)
    graph.add_node("agent", agent_node)
    graph.add_node("tools", tools_node)
    graph.add_node("finalize", finalize_node)
    graph.add_node("finalize_fallback", finalize_fallback_node)

    graph.set_entry_point("agent")
    graph.add_conditional_edges("agent", route_after_agent, {
        "tools": "tools",
        "finalize": "finalize",
        "finalize_fallback": "finalize_fallback",
    })
    graph.add_edge("tools", "agent")
    graph.add_edge("finalize", END)
    graph.add_edge("finalize_fallback", END)

    return graph.compile()


def run_agentic_query_v2(question: str, tool_dispatch: dict,max_iteration:int = MAX_ITERATIONS) -> dict:
    llm_tracker.reset_query()

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

    graph = build_agent_graph(tool_dispatch,max_iterations=max_iteration)
    initial_state = {
        "question": question,
        "messages": [{"role": "user", "content": question}],
        "tool_calls_made": [],
        "iteration": 0,
        "final_answer": None,
        "stopped_reason": None,
        "pending_tool_calls":None,
    }
    result = graph.invoke(initial_state)

    return {
        "answer": result["final_answer"],
        "tool_calls_made": result["tool_calls_made"],
        "iterations": result["iteration"],
    }