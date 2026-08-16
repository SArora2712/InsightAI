"""Item 1 + Item 2 regression guards.

Item 1: expander/status header Material icons must render as glyphs (never as
ligature source text) — the theme override must cover the stExpanderIcon*
testids Streamlit uses for status state icons, so labels like "Show full
answer" / "Report complete" render clean with no leading garbage.

Item 2: status run indicators collapse to a single clean completed label with
NO itemized step-by-step breakdown beneath, across History (expander label),
Executive Report (status label), and Simulator (status label).
"""
import tempfile
from pathlib import Path

from streamlit.testing.v1 import AppTest

import agents.simulator.decision_simulator as sim_mod
import core.history as history_mod
import core.theme2 as theme2
from core.report_generator import EXECUTIVE_REPORT_STEPS
from core import report_generator

ROOT = Path(__file__).resolve().parents[1]
CHAT_PY = str(ROOT / "chat2.py")
HISTORY_PY = str(ROOT / "pages2" / "history.py")
EXECUTIVE_PY = str(ROOT / "pages2" / "executive_report.py")
SIMULATOR_PY = str(ROOT / "pages2" / "simulator.py")


def _auth(at):
    at.session_state["authenticated"] = True
    at.session_state["role"] = "admin"
    at.session_state["username"] = "admin"


# ---------------------------------------------------------------------------
# Item 1 — shared icon-font override
# ---------------------------------------------------------------------------

def test_theme_covers_all_header_icon_testids():
    src = Path(theme2.__file__).read_text(encoding="utf-8")
    # The fix must forbid ligature-text leaks on BOTH FontIcon testids, not
    # just stIconMaterial (status state icons use stExpanderIcon* instead).
    assert '[data-testid="stIconMaterial"]' in src
    assert '[data-testid^="stExpanderIcon"]' in src
    assert "Material Symbols Rounded" in src


# ---------------------------------------------------------------------------
# History — 3+ cards, each expander label clean, icon empty
# ---------------------------------------------------------------------------

def test_history_expander_labels_are_clean_for_multiple_cards(monkeypatch):
    monkeypatch.setattr(history_mod, "DB_PATH", Path(tempfile.mkdtemp()) / "history.db")
    history_mod.init_db()
    for i in range(3):
        cid = history_mod.create_conversation()
        history_mod.maybe_set_title_from_first_message(cid, f"Conversation {i}")
        history_mod.save_message(cid, "user", f"Question {i}")
        history_mod.save_message(
            cid, "assistant", f"Answer {i}", {
                "confidence": {"label": "High", "score": 0.9},
                "mode": "Workflow (v1)",
            }
        )

    at = AppTest.from_file(HISTORY_PY, default_timeout=120)
    _auth(at)
    at.run()
    assert not at.exception
    expanders = list(at.expander)
    assert len(expanders) >= 3
    for ex in expanders:
        assert ex.label == "Show full answer", f"garble/overlap in label: {ex.label!r}"
        assert ex.icon == "", "no icon param allowed (ligature leak source)"


# ---------------------------------------------------------------------------
# Executive Report — status label clean + no itemized breakdown
# ---------------------------------------------------------------------------

def _fake_exec_report(workflow_app, questions=None, progress=None):
    if progress is not None:
        for step in EXECUTIVE_REPORT_STEPS:
            progress(step)
    return {
        "generated_at": "2026-08-15T00:00:00+00:00",
        "data_as_of": "2026-08-15",
        "findings": [
            {
                "question": "What was total revenue by category?",
                "answer": "Beverages led revenue.",
                "confidence": {"label": "High", "score": 0.85},
                "critique": {"has_issues": False, "severity": "none",
                             "findings": [], "verdict": ""},
                "conflict_detected": False,
            }
        ],
        "summary": "Executive summary prose.",
        "recommendations": "Recommendation prose.",
    }


def test_executive_report_status_clean_no_itemized_breakdown(monkeypatch):
    monkeypatch.setattr(report_generator, "generate_executive_report", _fake_exec_report)
    at = AppTest.from_file(EXECUTIVE_PY, default_timeout=180)
    _auth(at)
    at.session_state["executive_report"] = None
    at.run()
    assert not at.exception
    # Click "Generate report" to drive the live status block.
    at.button[0].click()
    at.run()
    assert not at.exception, [str(e.value)[:200] for e in at.exception]

    statuses = list(at.status)
    assert statuses, "status widget must render while/after generating"
    assert statuses[0].label == "Report complete"
    assert statuses[0].icon == ":material/check:"

    html = " ".join(m.value for m in at.markdown)
    assert "<div class=\"ia-steps\">" not in html
    assert "<div class=\"ia-step" not in html
    assert "<span class=\"ia-step-icon" not in html
    assert "Executive summary prose." in html


# ---------------------------------------------------------------------------
# Simulator — status label clean
# ---------------------------------------------------------------------------

def test_simulator_status_clean_no_itemized_breakdown(monkeypatch):
    result = {
        "error": "",
        "scenario": {"metric": "Price", "target": "Beverages", "change_percent": 10.0},
        "computed": {
            "current_revenue": 448386633,
            "projected_revenue": 460000000,
            "revenue_delta_pct": 2.9,
            "current_avg_price": 4.874,
        },
        "answer": "Projection answer prose.",
    }
    monkeypatch.setattr(sim_mod, "run_decision_simulator", lambda q: result)

    at = AppTest.from_file(SIMULATOR_PY, default_timeout=180)
    _auth(at)
    at.session_state["simulator_history"] = []
    at.run()
    assert not at.exception
    at.text_input[0].set_value("Increase Beverages price by 10%")
    at.button[0].click()
    at.run()
    assert not at.exception, [str(e.value)[:200] for e in at.exception]

    statuses = list(at.status)
    assert statuses, "status widget must render while/after running"
    assert statuses[0].label == "Projection complete"
    assert statuses[0].icon == ":material/check:"
    html = " ".join(m.value for m in at.markdown)
    assert "<div class=\"ia-steps\">" not in html
    assert "<div class=\"ia-step" not in html
    assert "<span class=\"ia-step-icon" not in html