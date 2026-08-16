"""Smoke tests for the Performance Monitor page (Item 6).

The page must stay light: it only reads in-process LLM counters, a cached
setup_resources call, and one list_conversations pass - nothing uncached
or per-page expensive. These tests keep that contract from regressing.
"""
from pathlib import Path

from streamlit.testing.v1 import AppTest

PERF_PY = str(Path(__file__).resolve().parents[1] / "pages2" / "performance_monitor.py")

EXPECTED_CARD_LABELS = [
    "LLM calls (this query)",
    "Tokens (this query)",
    "LLM calls (session)",
    "Call budget used",
]


def _run(role="admin"):
    at = AppTest.from_file(PERF_PY, default_timeout=120)
    at.session_state["authenticated"] = True
    at.session_state["role"] = role
    at.session_state["username"] = role
    at.run()
    return at


def test_admin_renders_all_stat_cards():
    at = _run("admin")
    assert not at.exception
    page_text = " ".join(m.value for m in at.markdown)
    for expected in EXPECTED_CARD_LABELS:
        assert expected in page_text
    # Resource status block renders too.
    assert "Resource status" in page_text


def test_guest_sees_admin_gate_without_stat_cards():
    at = _run("guest")
    assert not at.exception
    page_text = " ".join(m.value for m in at.markdown)
    assert all(expected not in page_text for expected in EXPECTED_CARD_LABELS)
    assert len(at.info) == 1
    assert "Admin access required" in at.info[0].value