"""Unit tests for the sequential step-progress indicator (Fix 2).

Guards the state machine contract: exactly one active step at any non-terminal
state, and a step never becomes active before its predecessor in the declared
call order (SQL → doc retrieval → synthesis → critique).
"""
import pytest

from core.progress import (
    StepTracker,
    PROCESSING_STEPS,
    STATE_DONE,
    STATE_ACTIVE,
    STATE_PENDING,
    render_steps_html,
)

EXPECTED_ORDER = [
    "Run SQL query",
    "Search documents",
    "Synthesize answer",
    "Review answer",
]


def test_declared_order_matches_call_order():
    assert PROCESSING_STEPS == EXPECTED_ORDER


def test_initial_state_one_active_rest_pending():
    t = StepTracker()
    snap = t.snapshot()
    assert t.active_count() == 1
    states = [s for _, s in snap]
    assert states == [STATE_ACTIVE] + [STATE_PENDING] * 3


def test_only_one_active_through_every_transition():
    t = StepTracker()
    assert t.active_count() == 1
    for step in EXPECTED_ORDER:
        t.advance(step)
        assert t.active_count() == 1, f"more than one active after {step}"
    # Terminal: the last step stays active until the run completes.
    assert t.active == EXPECTED_ORDER[-1]
    t.complete()
    assert t.active_count() == 0


def test_advance_marks_previous_steps_done():
    t = StepTracker()
    t.advance("Synthesize answer")
    states = {label: s for label, s in t.snapshot()}
    assert states["Run SQL query"] == STATE_DONE
    assert states["Search documents"] == STATE_DONE
    assert states["Synthesize answer"] == STATE_ACTIVE
    assert states["Review answer"] == STATE_PENDING


def test_complete_marks_all_done():
    t = StepTracker()
    t.complete()
    assert t.active_count() == 0
    assert all(s == STATE_DONE for _, s in t.snapshot())


def test_advance_ignores_backwards_and_unknown_steps():
    t = StepTracker()
    t.advance("Review answer")  # jump to the last step
    assert t.active == EXPECTED_ORDER[-1]
    # Re-advancing to an earlier step must not un-move the pointer.
    t.advance("Run SQL query")
    assert t.active == EXPECTED_ORDER[-1]
    states = [s for _, s in t.snapshot()]
    assert states == [STATE_DONE] * (len(EXPECTED_ORDER) - 1) + [STATE_ACTIVE]
    t2 = StepTracker()
    t2.advance("Not a real step")
    assert t2.snapshot()[0][1] == STATE_ACTIVE
    assert t2.active == EXPECTED_ORDER[0]


def test_render_html_single_active_and_done_checkmarks():
    t = StepTracker()
    t.advance("Search documents")
    html = render_steps_html(t)
    # Exactly one active row.
    assert html.count("ia-step active") == 1
    assert html.count("ia-step done") == 1
    assert html.count("ia-step pending") == 2
    # Done row uses a checkmark, active row uses the spinner.
    assert "&#10003;" in html
    assert "ia-spinner" in html
    # Order of labels in the rendered rows matches the declared call order.
    label_positions = [html.find(label) for label in EXPECTED_ORDER]
    assert label_positions == sorted(label_positions)
    assert -1 not in label_positions


def test_render_html_after_complete_no_spinner():
    t = StepTracker()
    t.complete()
    html = render_steps_html(t)
    assert html.count("ia-step active") == 0
    assert "ia-spinner" not in html
    assert html.count("ia-step done") == len(PROCESSING_STEPS)