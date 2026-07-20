"""
InsightAI - Source-Conflict Reconciler 

Combines whatever agent results are present into one coherent answer, AND
explicitly detects when sources disagree on the same fact rather than
silently picking one - surfacing the disagreement to the user instead.
"""
import json
import re

from core.llm_client import call_llm

RECONCILER_SYSTEM_PROMPT = """You are a business analyst assistant combining results from multiple \
internal tools into one answer for the user.

You may receive results from up to three sources:
- Document RAG: internal company documents
- SQL: the company's structured sales database
- Web: live internet search

Your job has two parts:

1. CHECK FOR CONFLICTS: Do any two sources state a DIFFERENT, CONTRADICTORY fact about the SAME thing \
(e.g. one says $92M revenue, another says $75M for the same category)? Sources covering DIFFERENT aspects \
of a question (one gives internal context, another gives external market data) are NOT a conflict - that's \
complementary information and should just be merged normally.

2. WRITE THE ANSWER:
   - If NO conflict: write one coherent answer combining all available sources, attributing each piece of \
information in parentheses, e.g. (from internal documents), (from sales data), (from web search).
   - If a conflict EXISTS: explicitly state both conflicting claims and which source each came from, rather \
than silently picking one. Do not try to guess which one is "right."

Respond with ONLY a JSON object in this exact shape, nothing else:
{
  "conflict_detected": true or false,
  "conflict_summary": "one sentence describing the conflict, or null if none",
  "answer": "the full answer text, written per the rules above"
}
"""

CONFLICT_CHECK_SYSTEM_PROMPT = """You are checking whether multiple data sources disagree on the same fact.

You will be given results from up to three sources... [existing text]

Check ONLY for genuine contradictions: two sources stating a DIFFERENT, CONTRADICTORY fact about the SAME \
thing, over the SAME time period and SAME scope. 

IMPORTANT: Before flagging a conflict, check whether the numbers actually refer to the same thing. \
"Total revenue" (all-time), "2023 revenue" (one year), and "Q4 2023 revenue" (one quarter) are \
DIFFERENT metrics, not contradictions, even if a user's question was ambiguous about which one they meant. \
If sources appear to disagree only because they answered different sub-questions or different time scopes, \
that is NOT a conflict - note the scope difference in your summary if relevant, but set conflict_detected to false.

Sources covering DIFFERENT aspects of a question are NOT a conflict...[rest unchanged]
"""

RECONCILER_SYSTEM_PROMPT = """You are a business analyst assistant combining results from multiple \
internal tools into one answer for the user.

... (existing content unchanged) ...

# in RECONCILER_SYSTEM_PROMPT (synthesizer.py) and AGENT_SYSTEM_PROMPT (agent.py):
"IMPORTANT: Report only what the sources actually state - do NOT add your own strategic \
recommendations or opinions unless explicitly asked. However, you MUST still write your answer \
as clear, natural prose sentences, not as raw JSON or data dumps. Synthesizing facts into readable \
sentences is required; adding unsolicited opinions is not."""

def _format_available_results(rag_result, sql_result, web_result) -> str:
    blocks = []

    if rag_result and rag_result.get("answer"):
        blocks.append(f"[Document RAG result]\n{rag_result['answer']}")

    if sql_result and not sql_result.get("error") and sql_result.get("row_count", 0) > 0:
        rows_preview = sql_result["rows"][:10]
        blocks.append(
            f"[SQL result] Query: {sql_result['sql']}\n"
            f"Columns: {sql_result['columns']}\n"
            f"Rows ({sql_result['row_count']} total, showing up to 10): {rows_preview}"
        )
    elif sql_result and sql_result.get("row_count", 0) == 0:
        blocks.append("[SQL result] Query ran successfully but returned no matching rows.")

    if web_result and web_result.get("answer"):
        sources_str = ", ".join(s["url"] for s in web_result.get("sources", [])[:3])
        blocks.append(f"[Web search result]\n{web_result['answer']}\nSources: {sources_str}")

    return "\n\n".join(blocks) if blocks else "No results were returned from any source."

def _parse_reconciler_output(raw_output: str, fallback_text: str) -> dict:
    """Extract the structured JSON; on any parse failure, degrade gracefully
    to a plain-answer response with conflict detection simply unavailable
    rather than crashing the whole pipeline over a formatting slip."""
    text = raw_output.strip()
    fence_match = re.search(r"```(?:json)?\s*(.*?)```", text, flags=re.DOTALL)
    if fence_match:
        text = fence_match.group(1).strip()

    try:
        parsed = json.loads(text)
        return {
            "conflict_detected": bool(parsed.get("conflict_detected", False)),
            "conflict_summary": parsed.get("conflict_summary"),
            "answer": parsed.get("answer", fallback_text),
        }
    except (json.JSONDecodeError, AttributeError):
        # Graceful degradation: treat the raw output as the answer, no known conflict
        return {"conflict_detected": False, "conflict_summary": None, "answer": raw_output}


def synthesize_final_answer(question: str, rag_result: dict, sql_result: dict, web_result: dict) -> dict:
    """
    Returns:
        {
            "answer": str,
            "conflict_detected": bool,
            "conflict_summary": str | None,
        }
    """
    context = _format_available_results(rag_result, sql_result, web_result)
    prompt = f"""Available results:

    {context}

    ---

    User's question: {question}

    Respond with the JSON object described in your instructions."""

    raw_output = call_llm(RECONCILER_SYSTEM_PROMPT, prompt)
    
    return _parse_reconciler_output(raw_output, fallback_text=raw_output)

def detect_conflict(rag_result: dict, sql_result: dict, web_result: dict) -> dict:
    """
    Standalone conflict check, decoupled from answer generation - used by
    Agent mode, which already has its own LLM-written answer from the tool
    loop and just needs to know whether the sources it gathered disagree,
    without regenerating a second competing answer.
    """
    context = _format_available_results(rag_result, sql_result, web_result)
    raw_output = call_llm(CONFLICT_CHECK_SYSTEM_PROMPT, context)

    text = raw_output.strip()
    fence_match = re.search(r"```(?:json)?\s*(.*?)```", text, flags=re.DOTALL)
    if fence_match:
        text = fence_match.group(1).strip()
    try:
        parsed = json.loads(text)
        return {
            "conflict_detected": bool(parsed.get("conflict_detected", False)),
            "conflict_summary": parsed.get("conflict_summary"),
        }
    except (json.JSONDecodeError, AttributeError):
        return {"conflict_detected": False, "conflict_summary": None}