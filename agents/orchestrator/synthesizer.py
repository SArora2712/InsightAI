"""
InsightAI - Source-Conflict Reconciler 

Combines whatever agent results are present into one coherent answer, AND
explicitly detects when sources disagree on the same fact rather than
silently picking one - surfacing the disagreement to the user instead.
"""
import json
import re

from core.llm_client import call_llm
from core.text_utils import ensure_prose
from core.logging_util import get_logger

logger = get_logger("agents.orchestrator.synthesizer")
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

IMPORTANT: Report only what the sources actually state - do NOT add your own strategic \
recommendations or opinions unless explicitly asked. However, you MUST still write your answer \
as clear, natural prose sentences, not as raw JSON or data dumps. Synthesizing facts into readable \
sentences is required; adding unsolicited opinions is not.

CRITICAL: The "answer" value must be a plain sentence or short paragraph a person would read aloud - \
never JSON, key-value pairs, code fences, or bullet-structured data. If you find yourself writing \
curly braces or a colon-separated list inside "answer", stop and rewrite it as prose.

FORMATTING RULE: Write every number and figure as plain text. NEVER wrap any number, dollar amount, \
or metric in backticks, asterisks, or any other code/emphasis formatting - for example write \
"$92.2M" not "`$92.2M`" or "*92.2M*". No markdown at all.

CRITICAL: If conflict_detected is true, conflict_summary must never be null - always populate it \
with one sentence naming both figures and their sources.

Examples:

Scope mismatch (NOT a conflict): Document RAG states "2023 revenue was $33.1M." SQL states \
"Q4 2023 revenue was $2.92M." These refer to different periods (full year vs. one quarter) - \
set conflict_detected to false, note the scope difference in the summary.

Genuine conflict (IS a conflict): Document RAG states "2023 revenue was $33.1M." SQL states \
"2023 revenue was $50.2M." Both explicitly refer to the same year - this is a real contradiction. \
Set conflict_detected to true even though the scope-check above tells you to look for scope \
mismatches first. A matching scope does not excuse a numeric disagreement. The answer should read: \
"Our internal report shows 2023 revenue at $33.1M, while the sales database shows $50.2M for the \
same year — these figures conflict and should be reconciled with the finance team." Note this is \
plain prose, not JSON, even though the underlying data is structured.

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

Examples:

Scope mismatch (NOT a conflict): Document RAG states "2023 revenue was $33.1M." SQL states \
"Q4 2023 revenue was $2.92M." These refer to different periods (full year vs. one quarter) - \
set conflict_detected to false, note the scope difference in the summary.

Genuine conflict (IS a conflict): Document RAG states "2023 revenue was $33.1M." SQL states \
"2023 revenue was $50.2M." Both explicitly refer to the same year - this is a real contradiction. \
Set conflict_detected to true even though the scope-check above tells you to look for scope \
mismatches first. A matching scope does not excuse a numeric disagreement.
"""

ANSWER_ONLY_SYSTEM_PROMPT = """You are a business analyst assistant writing an answer for the user \
based on results from internal tools (Document RAG, SQL, Web search).

You will be told whether the sources conflict - do not re-evaluate this yourself, just write \
around the given answer.

- If told there is NO conflict: write one coherent answer combining all available sources, \
attributing each piece of information in parentheses, e.g. (from internal documents), (from sales data).
- If told there IS a conflict: explicitly state both conflicting claims and which source each \
came from. Do not try to guess which one is "right."

Report only what the sources actually state - do not add strategic recommendations or opinions \
unless explicitly asked. Write in clear, natural prose sentences - never JSON, code fences, or \
bullet-structured data.

FORMATTING RULE: Write every number and figure as plain text. NEVER wrap any number, dollar amount, \
or metric in backticks, asterisks, or any other code/emphasis formatting - for example write \
"28.86" not "`28.86`" or "*28.86*". No markdown at all.

CRITICAL: Never state a specific number, metric, category, or business term unless it appears \
verbatim or is directly computed from the source results provided above. If a source is missing, \
empty, or irrelevant to part of the question, say so plainly rather than filling the gap with a \
plausible-sounding figure from general knowledge.

CRITICAL: If the source data includes both a raw value (e.g. a dollar amount) and a derived ratio \
(e.g. a percentage), cite the raw value as the primary figure in your answer - the ratio can support \
it, but should not replace it. Never state a decimal fraction (like 0.11) without converting it to a \
percentage (11%) if you mention it at all.

Respond with ONLY the answer text. No JSON, no preamble, no formatting."""

def _format_sql_rows(columns: list, rows: list[dict], limit: int = 10) -> str:
    """
    Renders SQL rows as clean, human-readable lines instead of raw dict
    repr with unformatted floats - reduces the chance of an LLM misreading
    magnitude (e.g. mistaking $48.3M for $48 billion) when re-expressing
    the numbers as prose.
    """
    lines = []
    for row in rows[:limit]:
        parts = []
        for col in columns:
            val = row.get(col)
            if isinstance(val, float):
                parts.append(f"{col}: {val:,.2f}")
            elif isinstance(val, int):
                parts.append(f"{col}: {val:,}")
            else:
                parts.append(f"{col}: {val}")
        lines.append("  - " + ", ".join(parts))
    return "\n".join(lines)


def _format_available_results(rag_result, sql_result, web_result) -> str:
    blocks = []

    if rag_result and rag_result.get("answer"):
        blocks.append(f"[Document RAG result]\n{rag_result['answer']}")

    if sql_result and not sql_result.get("error") and sql_result.get("row_count", 0) > 0:
        formatted_rows = _format_sql_rows(sql_result["columns"], sql_result["rows"])
        blocks.append(
            f"[SQL result] Query: {sql_result['sql']}\n"
            f"({sql_result['row_count']} total rows, showing up to 10)\n{formatted_rows}"
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
    context = _format_available_results(rag_result, sql_result, web_result)

    prompt = f"""Available results:

{context}

---

User's question: {question}

Analyze the sources for conflicts and write the final answer now."""

    raw_output = call_llm(RECONCILER_SYSTEM_PROMPT, prompt)

    def fallback():
        # If the LLM can't produce structured JSON, degrade to a plain answer
        # without staging a conflict claim (does not crash the pipeline).
        return {"conflict_detected": False, "conflict_summary": None, "answer": raw_output or ""}

    parsed = _parse_reconciler_output(raw_output or "", raw_output or "") if raw_output else fallback()

    return {
        "answer": parsed["answer"],
        "conflict_detected": parsed["conflict_detected"],
        "conflict_summary": parsed["conflict_summary"],
    }
def detect_conflict(rag_result: dict, sql_result: dict, web_result: dict) -> dict:

    
    outputs = {
        "rag": rag_result,
        "sql": sql_result,
        "web": web_result,
    }

    for source, raw_output in outputs.items():
        if raw_output is None:
            logger.debug("%s result is None", source)
            continue

        text = str(raw_output).strip()

        if not text:
            logger.debug("%s result is empty", source)
            continue

    context = _format_available_results(rag_result, sql_result, web_result)
    raw_output = call_llm(CONFLICT_CHECK_SYSTEM_PROMPT, context)

    text = (raw_output or "").strip()
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