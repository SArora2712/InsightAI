"""Regression tests for the completed-state summary line (new Item 2 design).

After a live run the assistant message renders a SINGLE clean "Analysis
complete" line — no expander, no itemized step-by-step breakdown. The line
appears exactly once per answered message, and only when the message was
produced by a live run (carries processing_steps).
"""
from pathlib import Path

from streamlit.testing.v1 import AppTest

from core.progress import PROCESSING_STEPS

CHAT_PY = str(Path(__file__).resolve().parents[1] / "chat2.py")


def _run(messages):
    at = AppTest.from_file(CHAT_PY, default_timeout=180)
    at.session_state["authenticated"] = True
    at.session_state["role"] = "admin"
    at.session_state["username"] = "admin"
    at.session_state["conversation_id"] = None
    at.session_state["messages"] = messages
    at.run()
    assert not at.exception, [str(e.value)[:200] for e in at.exception]
    return at


def _analysis_lines(at) -> list[str]:
    return [m.value for m in at.markdown if "Analysis complete" in m.value]


def _step_blocks(at) -> list[str]:
    return [m.value for m in at.markdown if '<div class="ia-steps">' in m.value]


def _assignment():
    return {
        "role": "assistant",
        "content": "A complete answer.",
        "meta": {},
        "processing_steps": list(PROCESSING_STEPS),
    }


def test_completed_run_renders_single_clean_line_no_breakdown():
    at = _run(
        [
            {"role": "user", "content": "Hello", "meta": None},
            _assignment(),
        ]
    )
    lines = _analysis_lines(at)
    assert len(lines) == 1, "exactly one 'Analysis complete' line per run"
    html = lines[0]
    # The line is a clean static label — never a step-by-step list.
    assert "Analysis complete" in html
    assert "✓" in html
    assert _step_blocks(at) == []
    # No collapsible "Analysis complete" expander remains (nothing to expand into).
    assert all("Analysis complete" not in (e.label or "") for e in at.expander)


def test_multiple_answered_messages_each_render_one_clean_line():
    at = _run(
        [
            {"role": "user", "content": "Q1", "meta": None},
            _assignment(),
            {"role": "user", "content": "Q2", "meta": None},
            _assignment(),
        ]
    )
    assert len(_analysis_lines(at)) == 2
    assert _step_blocks(at) == []


def test_no_completed_line_without_processing_steps():
    at = _run(
        [
            {"role": "user", "content": "Hello", "meta": None},
            {"role": "assistant", "content": "Plain answer.", "meta": {}},
        ]
    )
    assert _analysis_lines(at) == []
    assert _step_blocks(at) == []


def test_live_processing_label_is_not_an_itemized_list():
    # The header must be driven by the status label, never a vertical checklist.
    # (The theme's CSS mentions .ia-step etc., so assert on *rendered* markup.)
    at = _run(
        [
            {"role": "user", "content": "Hello", "meta": None},
            _assignment(),
        ]
    )
    html = " ".join(m.value for m in at.markdown)
    # Rendered step-list markup only — the theme CSS mentions the class names.
    assert "<div class=\"ia-steps\">" not in html
    assert "<div class=\"ia-step" not in html
    assert "<span class=\"ia-step-icon" not in html
    assert "<span class=\"ia-spinner\"" not in html
    assert "Running SQL query" not in html