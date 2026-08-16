"""AppTest tests for the Simulator analysis header (Fix 6).

The Analysis section is rendered as a clear section header (matching the
app's other headers, e.g. "Recent insights") with a subtle top divider, while
the warning banner below stays untouched.
"""
from pathlib import Path

from streamlit.testing.v1 import AppTest

SIMULATOR_PY = str(Path(__file__).resolve().parents[1] / "pages2" / "simulator.py")

RESULT = {
    "error": "",
    "scenario": {
        "metric": "Price",
        "target": "Beverages",
        "change_percent": 10.0,
    },
    "computed": {
        "current_revenue": 448386633,
        "projected_revenue": 461223000,
        "revenue_delta_pct": 2.9,
        "current_avg_price": 4.874,
    },
    "answer": (
        "If you increase the price of Beverages by 10%, revenue would grow by "
        "an estimated 2.9% while holding everything else constant."
    ),
}


def _run_simulator():
    at = AppTest.from_file(SIMULATOR_PY, default_timeout=120)
    at.session_state["authenticated"] = True
    at.session_state["role"] = "admin"
    at.session_state["username"] = "admin"
    at.session_state["simulator_history"] = [RESULT]
    at.session_state["simulator_last_run"] = "Aug 15, 2026"
    at.run()
    assert not at.exception
    return at


def _all_markdown(at) -> list[str]:
    return [m.value for m in at.markdown]


def test_analysis_rendered_as_section_header():
    at = _run_simulator()
    md = _all_markdown(at)
    assert any("sim-section-header" in x for x in md)
    assert any(">Analysis</div>" in x for x in md)


def test_analysis_answer_still_rendered():
    at = _run_simulator()
    md = " ".join(_all_markdown(at))
    assert RESULT["answer"] in md


def test_answer_markdown_has_no_backtick_code_spans():
    """Item 1 regression: generated prose that backtick-wraps SOME figures
    while leaving others plain must render fully plain (the old mixed
    teal-monospace / black-text look within one sentence)."""
    at = AppTest.from_file(SIMULATOR_PY, default_timeout=120)
    at.session_state["authenticated"] = True
    at.session_state["role"] = "admin"
    at.session_state["username"] = "admin"

    mixed = dict(RESULT)
    mixed["answer"] = (
        "Using the current average unit price of `28.86`, the projected revenue "
        "would be 13,519,223.74 `units` * 28.86 = $390,096,370.86"
    )
    at.session_state["simulator_history"] = [mixed]
    at.session_state["simulator_last_run"] = "Aug 15, 2026"
    at.run()
    assert not at.exception

    md = _all_markdown(at)
    # The injected <style>/<script> block legitimately contains backtick JS
    # template literals, so scope the check to elements that carry the answer
    # figures: none may contain a markdown code span, a leaked backslash
    # escape ("\*"), or a garbled fragment.
    figures = ("28.86", "13,519,223.74", "$390,096,370.86")
    answer_els = [x for x in md if any(fig in x for fig in figures)]
    assert answer_els, "answer figures not found in rendered markdown"
    for el in answer_els:
        assert "`" not in el, f"code span survived in: {el[:120]!r}"
        assert "\\" not in el, f"backslash escape leaked in: {el[:120]!r}"
    text = " ".join(md)
    assert "28.86" in text
    assert "13,519,223.74" in text
    assert "$390,096,370.86" in text


def test_answer_formula_uses_multiplication_sign_not_backslash():
    """Regression: arithmetic like "41.67*2,427,361" must render with a clean
    × sign - never a backslash-asterisk escape."""
    at = AppTest.from_file(SIMULATOR_PY, default_timeout=120)
    at.session_state["authenticated"] = True
    at.session_state["role"] = "admin"
    at.session_state["username"] = "admin"

    mixed = dict(RESULT)
    mixed["answer"] = (
        "The current average unit price is 37.97, so a 10% increase gives "
        "37.97 + (37.97*0.10) = 41.67. The projected revenue is "
        "41.67*2,427,361 = 101,379,502.60."
    )
    at.session_state["simulator_history"] = [mixed]
    at.session_state["simulator_last_run"] = "Aug 15, 2026"
    at.run()
    assert not at.exception

    md = _all_markdown(at)
    answer_els = [x for x in md if "41.67" in x]
    assert answer_els
    for el in answer_els:
        assert "\\" not in el, f"backslash leaked in: {el[:120]!r}"
        assert "*" not in el, f"raw asterisk leaked in: {el[:120]!r}"
    # The fully formatted formulas read with the multiplication sign.
    assert any("(37.97×0.10)" in x for x in md)
    assert any("41.67×2,427,361" in x for x in md)


def test_warning_banner_unchanged():
    at = _run_simulator()
    md = " ".join(_all_markdown(at))
    assert "straight-line projection holding all else constant" in md