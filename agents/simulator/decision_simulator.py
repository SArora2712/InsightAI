"""
InsightAI - AI Decision Simulator.
Answers "what-if" business questions using REAL current data + transparent,
code-computed math - not LLM-guessed projections. Scope: straight-line
projections only (no price elasticity modeling - see design notes in
project handover for why that's a deliberate boundary, not an oversight).
"""
import json
import re
import sys
from pathlib import Path


from core.llm_client import call_llm


from agents.sql_agent.executor import execute_sql
from agents.sql_agent.validator import validate_sql, SQLValidationError


PARSE_SCENARIO_PROMPT = """You are parsing a business "what-if" question into a structured scenario.

Extract:
- "metric": what's being changed - "price" or "quantity"
- "target": a product category name (e.g. "Beverages"), or "all" for company-wide
- "change_percent": the percentage change as a number (positive = increase, negative = decrease)

Respond with ONLY a JSON object:
{"metric": "price", "target": "Beverages", "change_percent": 10}

If not a numeric what-if about price or quantity, respond:
{"metric": null, "target": null, "change_percent": null}
"""

NARRATE_RESULT_PROMPT_TEMPLATE = """A business analyst asked: "{question}"

ALREADY-COMPUTED result, based on real current data:

Current state:
- Category: {target}
- Current revenue: ${current_revenue:,.2f}
- Current quantity sold: {current_quantity:,}
- Current average unit price: ${current_avg_price:.2f}

Scenario applied: {metric} changed by {change_percent:+.1f}%

Projected result (straight-line, holding all else constant):
- Projected revenue: ${projected_revenue:,.2f}
- Revenue change: ${revenue_delta:,.2f} ({revenue_delta_pct:+.1f}%)

Write a brief, clear narrative explaining this projection. Explicitly state this is a straight-line \
projection assuming volume/behavior doesn't change in response (no elasticity modeled) - be upfront \
about this limitation. Do not invent any numbers beyond what's given above."""


def _get_category_baseline(target: str) -> dict | None:
    if target.lower() == "all":
        sql = """SELECT SUM(OD.UnitPrice * OD.Quantity * (1 - OD.Discount)) AS Revenue,
                         SUM(OD.Quantity) AS Quantity
                  FROM "Order Details" OD"""
    else:
        sql = f"""SELECT SUM(OD.UnitPrice * OD.Quantity * (1 - OD.Discount)) AS Revenue,
                         SUM(OD.Quantity) AS Quantity
                  FROM "Order Details" OD
                  JOIN Products P ON OD.ProductID = P.ProductID
                  JOIN Categories C ON P.CategoryID = C.CategoryID
                  WHERE C.CategoryName = '{target}'"""
    try:
        validated = validate_sql(sql)
    except SQLValidationError:
        return None
    try:
        result = execute_sql(validated)
    except Exception:
        return None
    if not result["rows"] or result["rows"][0]["Revenue"] is None:
        return None
    row = result["rows"][0]
    revenue, quantity = row["Revenue"], row["Quantity"]
    return {"revenue": revenue, "quantity": quantity, "avg_price": revenue / quantity if quantity else 0}


def _parse_scenario(question: str) -> dict:
    raw = call_llm(PARSE_SCENARIO_PROMPT, question)
    text = raw.strip()
    fence_match = re.search(r"```(?:json)?\s*(.*?)```", text, flags=re.DOTALL)
    if fence_match:
        text = fence_match.group(1).strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return {"metric": None, "target": None, "change_percent": None}


def run_decision_simulator(question: str) -> dict:
    scenario = _parse_scenario(question)
    if not scenario.get("metric") or not scenario.get("target"):
        return {"question": question, "answer": None, "scenario": None, "computed": None,
                 "error": "Could not parse this as a numeric what-if scenario about price or quantity."}

    baseline = _get_category_baseline(scenario["target"])
    if baseline is None:
        return {"question": question, "answer": None, "scenario": scenario, "computed": None,
                 "error": f"No data found for target '{scenario['target']}'."}

    change_pct = scenario["change_percent"] / 100.0
    projected_revenue = baseline["revenue"] * (1 + change_pct)
    revenue_delta = projected_revenue - baseline["revenue"]
    revenue_delta_pct = (revenue_delta / baseline["revenue"] * 100) if baseline["revenue"] else 0

    computed = {
        "current_revenue": baseline["revenue"], "current_quantity": baseline["quantity"],
        "current_avg_price": baseline["avg_price"], "projected_revenue": projected_revenue,
        "revenue_delta": revenue_delta, "revenue_delta_pct": revenue_delta_pct,
    }

    narration_prompt = NARRATE_RESULT_PROMPT_TEMPLATE.format(question=question, target=scenario["target"], **computed, metric=scenario["metric"], change_percent=scenario["change_percent"])
    answer = call_llm("You are a precise business analyst assistant.", narration_prompt)

    return {"question": question, "answer": answer, "scenario": scenario, "computed": computed, "error": None}