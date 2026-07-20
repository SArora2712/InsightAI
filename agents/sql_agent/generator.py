"""
InsightAI - SQL Agent core: schema-linking -> NL->SQL generation -> validation
-> execution, with one retry on execution failure.
"""
import re
import sys
from pathlib import Path

from core.llm_client import call_llm

from agents.sql_agent.schema_linker import SchemaLinker
from validator import validate_sql, SQLValidationError
from prompts import build_sql_system_prompt, build_sql_prompt, build_retry_prompt
from executor import execute_sql, get_max_order_date, SQLExecutionError

MAX_RETRIES = 2

_linker = SchemaLinker()
_reference_date = None 

def _extract_sql(llm_output: str) -> str:
    """Strip markdown code fences if the model wraps its output despite instructions."""
    text = llm_output.strip()
    fence_match = re.search(r"```(?:sql)?\s*(.*?)```", text, flags=re.DOTALL | re.IGNORECASE)
    if fence_match:
        return fence_match.group(1).strip()
    return text


def run_sql_agent(question: str) -> dict:
    global _reference_date
    if _reference_date is None:
        _reference_date = get_max_order_date()
        print(f"[sql_agent] Dataset reference date (effective 'now'): {_reference_date}")

    system_prompt = build_sql_system_prompt(_reference_date)   # <- was the SQL_SYSTEM_PROMPT constant

    tables_used = _linker.retrieve(question)
    schema_context = _linker.retrieve_formatted(question)
    prompt = build_sql_prompt(question, schema_context)

    last_sql = None
    last_error = None
    for attempt in range(1, MAX_RETRIES + 2):
        if attempt == 1:
            raw_output = call_llm(system_prompt, prompt)              # <- use system_prompt, not SQL_SYSTEM_PROMPT
        else:
            retry_prompt = build_retry_prompt(question, schema_context, last_sql, last_error)
            raw_output = call_llm(system_prompt, retry_prompt)    

        sql = _extract_sql(raw_output)
        last_sql = sql

        try:
            validated_sql = validate_sql(sql)
        except SQLValidationError as e:
            last_error = f"Validation error: {e}"
            continue

        try:
            result = execute_sql(validated_sql)
            return {
                "question": question,
                "sql": validated_sql,
                "tables_used": tables_used,
                "columns": result["columns"],
                "rows": result["rows"],
                "row_count": result["row_count"],
                "execution_time_ms": result["execution_time_ms"],
                "attempts": attempt,
                "error": None,
            }
        except SQLExecutionError as e:
            last_error = str(e)
            continue

    # All attempts exhausted
    return {
        "question": question,
        "sql": last_sql,
        "tables_used": tables_used,
        "columns": [],
        "rows": [],
        "row_count": 0,
        "execution_time_ms": 0,
        "attempts": MAX_RETRIES + 1,
        "error": last_error,
    }