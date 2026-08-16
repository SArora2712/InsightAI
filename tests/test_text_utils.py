"""Unit tests for core.text_utils number/prose cleaning.

Regression for the "mixed teal monospace + plain text in one sentence" bug:
LLM answers intermittently wrap figures in backticks (rendered as code spans /
teal monospace by Streamlit) while leaving identical figures plain. clean_prose
must flatten ALL such spans so every number in a sentence renders identically -
and it must never leak backslash escapes (the "\*" regression) or delete prose
between a distant backtick pair.
"""
import core.text_utils as tu


def test_strip_inline_code_removes_short_code_spans():
    out = tu.strip_inline_code("a `28.86` and a `13,519,223.74` unit")
    assert out == "a 28.86 and a 13,519,223.74 unit"


def test_strip_inline_code_drops_stray_single_backtick():
    out = tu.strip_inline_code("uses `28.86 as the price")
    assert "`" not in out
    assert "28.86" in out


def test_strip_inline_code_does_not_swallow_wide_span():
    """A backtick pair far apart (or across a newline) must NOT delete the
    prose in between - the "soa1..." garble class of bug."""
    raw = "so `a 10% increase gives 37.97 + (37.97*0.10) = 41.67` next"
    out = tu.strip_inline_code(raw)
    assert "increase gives" in out
    assert "37.97 + (37.97*0.10) = 41.67" in out
    assert "`" not in out


def test_strip_inline_code_handles_empty():
    assert tu.strip_inline_code("") == ""
    assert tu.strip_inline_code(None) is None


def test_multiplication_mark_converts_lone_asterisks_to_x():
    out = tu.multiplication_mark("37.97 * 0.10 = 41.67 and 41.67*2,427,361")
    assert "×" in out
    assert "*" not in out
    assert "37.97 × 0.10 = 41.67 and 41.67×2,427,361" == out


def test_multiplication_mark_keeps_bold_markers():
    out = tu.multiplication_mark("**revenue** driver * 1.03")
    assert "**revenue**" in out
    assert "×" in out


def test_multiplication_mark_never_emits_backslash():
    out = tu.multiplication_mark("a * b")
    assert "\\" not in out


def test_clean_prose_flattens_backticks_and_asterisks_no_backslash():
    out = tu.clean_prose("`28.86` * 1.03 = `38.97`")
    assert "`" not in out
    assert "\\" not in out
    assert "×" in out
    assert "28.86" in out
    assert "38.97" in out


def test_same_sentence_mixed_styling_becomes_fully_plain():
    raw = (
        "Using the current average unit price of `28.86`, the projected revenue "
        "would be 13,519,223.74 `units` * 28.86 = $390,096,370.86"
    )
    out = tu.clean_prose(raw)
    assert "`" not in out
    assert "\\" not in out
    # Both occurrences of 28.86 survive - one was backtick-wrapped, one wasn't.
    assert out.count("28.86") == 2


def test_clean_prose_handles_empty():
    assert tu.clean_prose("") == ""
    assert tu.clean_prose(None) is None