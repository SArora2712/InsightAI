"""
InsightAI - Critique Agent.

Reviews the synthesized answer as an independent pass - a different LLM
call than the one that wrote the answer, mirroring a second human reviewer
rather than the same model grading its own homework in one breath.
Findings are ATTACHED alongside the answer, never used to silently trigger
a retry - surfacing an issue is more valuable than hiding it behind an
auto-correction attempt that isn't guaranteed to actually fix it.
"""
import json
import re
import sys
from pathlib import Path


from core.llm_client import call_llm

CRITIQUE_SYSTEM_PROMPT = """You are a critical reviewer checking a business analyst assistant's answer \
before it reaches the user. You did NOT write this answer - review it independently and skeptically.

Check for:
- Does the answer actually address the question that was asked, or does it drift off-topic?
- Does it claim anything NOT supported by the provided source data (overclaiming/fabrication)?
- Is it missing an obvious angle the available source data could have addressed but didn't?
- Is it appropriately hedged when the underlying data was weak/incomplete/conflicting?

Respond with ONLY a JSON object in this exact shape, nothing else:
{
  "has_issues": true or false,
  "severity": "none" or "minor" or "moderate" or "severe",
  "findings": ["short specific finding", ...],
  "verdict": "one sentence overall assessment"
}

If the answer is genuinely solid, set has_issues to false, severity to "none", and findings to an empty list \
- do not invent minor nitpicks just to have something to say."""


def _format_context_for_critique(question: str, answer: str, rag_result, sql_result, web_result) -> str:
    parts = [f"Original question: {question}", f"\nAnswer given to the user:\n{answer}", "\nSource data that was available:"]

    if rag_result and rag_result.get("answer"):
        parts.append(f"- Document RAG found: {rag_result['answer'][:400]}")
    if sql_result and sql_result.get("row_count", 0) > 0:
        parts.append(f"- SQL found {sql_result['row_count']} rows via: {sql_result['sql']}")
    elif sql_result:
        parts.append("- SQL was run but found no matching rows")
    if web_result and web_result.get("answer"):
        parts.append(f"- Web search found: {web_result['answer'][:400]}")
    if not any([rag_result, sql_result, web_result]):
        parts.append("- No sources were consulted")

    return "\n".join(parts)


def _parse_critique_output(raw_output: str) -> dict:
    text = raw_output.strip()
    fence_match = re.search(r"```(?:json)?\s*(.*?)```", text, flags=re.DOTALL)
    if fence_match:
        text = fence_match.group(1).strip()
    try:
        parsed = json.loads(text)
        return {
            "has_issues": bool(parsed.get("has_issues", False)),
            "severity": parsed.get("severity", "none"),
            "findings": parsed.get("findings", []),
            "verdict": parsed.get("verdict", ""),
        }
    except (json.JSONDecodeError, AttributeError):
        # Graceful degradation - critique is a bonus signal, never block the pipeline over a parse failure
        return {"has_issues": False, "severity": "none", "findings": [], "verdict": "Critique unavailable (parse error)."}


def critique_answer(question: str, answer: str, rag_result: dict, sql_result: dict, web_result: dict) -> dict:
    context = _format_context_for_critique(question, answer, rag_result, sql_result, web_result)
    prompt = f"""{context}

Review this answer per your instructions and respond with the JSON object."""

    raw_output = call_llm(CRITIQUE_SYSTEM_PROMPT, prompt)
    return _parse_critique_output(raw_output)