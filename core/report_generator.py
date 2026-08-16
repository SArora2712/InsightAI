"""
InsightAI - Executive Report generation.
Runs a fixed set of representative business questions through the real
orchestrator graph, then synthesizes the findings into summary and
recommendation sections. All numbers trace back to actual workflow_app
runs - nothing is invented at the synthesis stage.
"""
from datetime import datetime, timezone
import time

from core.llm_client import call_llm,llm_tracker
from agents.sql_agent.executor import get_max_order_date
from core.logging_util import get_logger

logger = get_logger("core.report_generator")

# Sequential pipeline stages surfaced to the Executive Report page via the same
# StepTracker component used by Chat (core/progress.py). Kept here, next to
# the pipeline that produces them, so the page never hard-codes the stages.
EXECUTIVE_REPORT_STEPS = [
    "Querying sales database",
    "Analyzing internal reports",
    "Gathering market context",
    "Compiling report",
]

_NODE_STEP_MAP = {
    "sql_agent": "Querying sales database",
    "rag_agent": "Analyzing internal reports",
    "web_agent": "Gathering market context",
}

# Repeated "Generate report" clicks are expensive (4 orchestrator runs + 2 LLM
# synthesis calls). Cache the final report for a short TTL so an immediate
# re-request is instant; the SQL + LLM caches already make it cheap regardless.
_REPORT_CACHE: dict = {}
_REPORT_CACHE_TTL_SECONDS = 120

STANDARD_QUESTIONS = [
    "What was total revenue by category, and which category is strongest?",
    "Is there a revenue decline mentioned in our reports, and is it reflected in the actual sales data?",
    "How did our sales perform, and how might current inflation affect future sales, based on our internal reports?",
    "How balanced is revenue across our top sales employees?",
]

SUMMARY_PROMPT = """You are writing the executive summary section of a business report for Northwind Traders.

Below are several already-answered analyst questions with their findings. Synthesize them into a concise \
executive summary (3-5 sentences) highlighting the most important takeaways for leadership.

CRITICAL: Do not invent any numbers, dates, or facts not present in the findings below. If the findings \
don't cover something, don't mention it."""

RECOMMENDATIONS_PROMPT = """Based on the findings below for Northwind Traders, write 2-4 specific, \
actionable recommendations for leadership.

CRITICAL: Ground every recommendation in something explicitly stated in the findings below. Do not \
invent data or suggest generic business advice unconnected to what's actually shown."""


def generate_executive_report(workflow_app, questions: list[str] = None, progress=None) -> dict:
    """Run the full report pipeline. `progress` is an optional callback
    receiving the next pipeline stage label (same StepTracker.advance contract
    as Chat); when provided, workflow runs are streamed so each completed
    agent node advances the UI's sequential indicator."""
    questions = questions or STANDARD_QUESTIONS
    cache_key = tuple(questions)
    now = time.time()
    cached = _REPORT_CACHE.get(cache_key)
    if cached is not None and now - cached[0] < _REPORT_CACHE_TTL_SECONDS:
        logger.debug("Returning cached executive report.")
        if progress is not None:
            progress("Compiling report")
        return cached[1]

    reference_date = get_max_order_date()
    if progress is not None:
        progress("Querying sales database")

    findings = []
    for q in questions:
        llm_tracker.reset_query()
        initial_state = {
            "query": q, "agents_needed": [], "rag_result": None, "sql_result": None,
            "web_result": None, "final_answer": None, "conflict_detected": None,
            "conflict_summary": None, "confidence": None, "critique": None,
        }

        if progress is None:
            result = workflow_app.invoke(initial_state)
        else:
            # stream_mode="updates" yields one event per completed node, so the
            # page can advance the sequential indicator as agents finish.
            result = dict(initial_state)
            for event in workflow_app.stream(initial_state, stream_mode="updates"):
                for node_name, payload in event.items():
                    step = _NODE_STEP_MAP.get(node_name)
                    if step:
                        progress(step)
                    if isinstance(payload, dict):
                        result.update(payload)

        findings.append({
            "question": q,
            "answer": result.get("final_answer") or "No answer generated.",
            "confidence": result.get("confidence") or {},
            "critique": result.get("critique") or {},
            "conflict_detected": result.get("conflict_detected", False),
            "conflict_summary": result.get("conflict_summary"),
        })

    if progress is not None:
        progress("Compiling report")

    findings_text = "\n\n".join(f"Q: {f['question']}\nA: {f['answer']}" for f in findings)

    summary = call_llm(SUMMARY_PROMPT, findings_text)
    recommendations = call_llm(RECOMMENDATIONS_PROMPT, findings_text)

    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "data_as_of": reference_date,
        "findings": findings,
        "summary": summary,
        "recommendations": recommendations,
    }

    _REPORT_CACHE[cache_key] = (now, report)
    return report