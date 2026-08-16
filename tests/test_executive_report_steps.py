"""Tests for the Executive Report step tracker (Item 3).

The report page must reuse the SAME StepTracker component as Chat
(core/progress.py) and drive it from the real pipeline stages. These tests
exercise generate_executive_report with a fake workflow_app (invoke + stream)
so the progress callback and result assembly are checked without any network.
"""
import pytest

from core import report_generator
from core.progress import StepTracker

EXPECTED_STEPS = [
    "Querying sales database",
    "Analyzing internal reports",
    "Gathering market context",
    "Compiling report",
]


class FakeWorkflow:
    def __init__(self, questions):
        self._questions = questions

    def invoke(self, state):
        return _final_state(state["query"])

    def stream(self, state, stream_mode="updates"):
        # Node events in orchestrator order, mirroring agents/orchestrator/graph.py.
        per = [
            {"router": {"agents_needed": ["sql", "document_rag", "web"]}},
            {"sql_agent": {"sql_result": {"question": state["query"], "rows": [], "row_count": 0}}},
            {"rag_agent": {"rag_result": {"answer": "doc hit"}}},
            {"web_agent": {"web_result": {"sources": [], "answer": "web hit"}}},
        ]
        final = _final_state(state["query"])
        per.append({"synthesize": {
            "final_answer": final["final_answer"],
            "conflict_detected": False, "conflict_summary": None,
        }})
        per.append({"confidence_critique": {
            "confidence": final["confidence"], "critique": final["critique"],
        }})
        yield from per


def _final_state(q):
    return {
        "final_answer": f"Answer for {q}",
        "conflict_detected": False,
        "conflict_summary": None,
        "confidence": {"score": 0.8, "label": "High", "reasons": []},
        "critique": {"has_issues": False, "severity": "none", "findings": [], "verdict": ""},
    }


@pytest.fixture(autouse=True)
def _no_llm_and_clean_cache(monkeypatch):
    monkeypatch.setattr(report_generator, "_REPORT_CACHE", {})
    monkeypatch.setattr(
        report_generator, "get_max_order_date", lambda: "2026-08-15"
    )
    monkeypatch.setattr(
        report_generator,
        "call_llm",
        lambda s, u, temperature=0.0, max_tokens=None: f"synthetic:{u[:20]}",
    )


def test_pipeline_steps_match_declaration():
    assert report_generator.EXECUTIVE_REPORT_STEPS == EXPECTED_STEPS


def test_progress_drives_every_step_and_finishes_done():
    seen = []
    tracker = StepTracker(steps=EXPECTED_STEPS)
    report = report_generator.generate_executive_report(
        FakeWorkflow(["q1", "q2"]),
        questions=["q1", "q2"],
        progress=lambda s: seen.append(s) or tracker.advance(s),
    )
    # First stage fires, then agent nodes (per question), then compiling.
    assert seen[0] == "Querying sales database"
    assert seen[-1] == "Compiling report"
    # Every declared step was reached; nothing else.
    assert set(seen) == set(EXPECTED_STEPS)
    # Terminal stage stays active until the page marks the run complete...
    assert tracker.active == "Compiling report"
    assert tracker.active_count() == 1
    # ...which is exactly what the page does (see executive_report.py).
    tracker.complete()
    assert tracker.active_count() == 0
    assert all(s == "done" for _, s in tracker.snapshot())


def test_progress_none_still_returns_full_report():
    tracker = StepTracker(steps=EXPECTED_STEPS)
    report = report_generator.generate_executive_report(
        FakeWorkflow(["q1", "q2"]), questions=["q1", "q2"], progress=tracker.advance
    )
    assert report["data_as_of"] == "2026-08-15"
    assert len(report["findings"]) == 2
    assert report["findings"][0]["question"] == "q1"
    assert report["findings"][0]["answer"] == "Answer for q1"
    assert report["summary"].startswith("synthetic:")
    assert report["recommendations"].startswith("synthetic:")


def test_invoke_and_stream_paths_agree():
    flat = report_generator.generate_executive_report(FakeWorkflow(["q1"]), questions=["q1"])
    stepped = report_generator.generate_executive_report(
        FakeWorkflow(["q1"]),
        questions=["q1"],
        progress=StepTracker(steps=EXPECTED_STEPS).advance,
    )
    assert flat["findings"] == stepped["findings"]
    assert flat["summary"] == stepped["summary"]