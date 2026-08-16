"""AppTest regression tests for the History page (Fix 4).

Every card must show a ONE-LINE truncated preview (~100 chars) with the full
answer available behind an expand/collapse toggle, and crucially the expanded
content must be bound to THAT card's own conversation (conversation_id) -
never a shared/duplicated answer (the old bug).
"""
import tempfile
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from core import history

HISTORY_PY = str(Path(__file__).resolve().parents[1] / "pages2" / "history.py")

# Distinct, long (>100 chars) answers so each one truncates to a unique preview.
ANSWERS = {
    "gamma": "Gamma scenario answer for the revenue forecast " * 4,
    "beta": "Beta scenario answer for the confectionary pricing " * 4,
    "alpha": "Alpha scenario answer for the beverage elasticity " * 4,
}


@pytest.fixture()
def seeded_db():
    history.DB_PATH = Path(tempfile.mkdtemp()) / "history.db"
    history.init_db()
    items = []
    for key, answer in ANSWERS.items():
        cid = history.create_conversation()
        history.maybe_set_title_from_first_message(cid, key)
        history.save_message(cid, "user", key)
        history.save_message(cid, "assistant", answer)
        items.append((key, cid, answer))
    yield items


def _run_history():
    at = AppTest.from_file(HISTORY_PY, default_timeout=120)
    at.session_state["authenticated"] = True
    at.session_state["role"] = "admin"
    at.session_state["username"] = "admin"
    at.run()
    assert not at.exception
    return at


def _all_markdown(at) -> list[str]:
    return [m.value for m in at.markdown]


def test_each_card_binds_expanded_text_to_its_own_answer(seeded_db):
    at = _run_history()
    md = _all_markdown(at)
    for _key, _cid, answer in seeded_db:
        # The full answer appears exactly once - in its own card's expander.
        # (rstrip: AppTest strips the trailing whitespace of the message.)
        assert sum(answer.rstrip() in x for x in md) == 1


def test_expanders_are_unique_and_ordered_per_card(seeded_db):
    at = _run_history()
    md = _all_markdown(at)
    # Newest-first render order: alpha was seeded last => newest => rendered first.
    expected_order = ["alpha", "beta", "gamma"]
    positions = []
    for key in expected_order:
        needle = ANSWERS[key].rstrip()
        idx = next(i for i, x in enumerate(md) if needle in x)
        positions.append(idx)
    # Strictly increasing => each expander sits inside its own card's position
    # (no card bleeding another card's answer).
    assert positions == sorted(positions)
    assert len(set(positions)) == len(positions)


def test_preview_is_single_line_truncated_per_card(seeded_db):
    at = _run_history()
    md = _all_markdown(at)
    assert all(len(a) > 100 for a in ANSWERS.values())
    for _key, _cid, answer in seeded_db:
        snippet = history.preview_snippet(answer, limit=100)
        preview_p = next(
            (x for x in md if 'class="hist-preview"' in x and snippet in x), None
        )
        assert preview_p is not None, "card truncated preview missing"
        # The preview paragraph holds only the truncated cut, not the full text.
        assert answer not in preview_p
        # And the full text lives in a separate (expander) markdown element.
        assert any(answer.rstrip() in x for x in md)


def test_short_answers_keep_verbatim_preview_without_ellipsis():
    assert history.preview_snippet("Short answer.") == "Short answer."
    assert "…" not in history.preview_snippet("Fin.")


def test_numbers_render_plain_no_code_spans(monkeypatch):
    """Item 1 regression: a stored answer that backtick-wraps SOME figures
    (teal monospace in Streamlit) while leaving others plain must render all
    numbers identically in both the card preview and the expanded answer."""
    history.DB_PATH = Path(tempfile.mkdtemp()) / "history.db"
    history.init_db()
    cid = history.create_conversation()
    history.maybe_set_title_from_first_message(cid, "price impact")
    raw = (
        "Using the current average unit price of `28.86`, the projected revenue "
        "would be 13,519,223.74 `units` * 28.86 = $390,096,370.86"
    )
    history.save_message(cid, "user", "simulate beverages price")
    history.save_message(cid, "assistant", raw)

    at = _run_history()
    assert not at.exception
    md = _all_markdown(at)
    # The injected <style>/<script> block legitimately contains backtick JS
    # template literals, so scope the check to elements that carry the answer
    # figures: preview + expander must be free of markdown code spans and
    # backslash-escape leaks.
    figures = ("28.86", "13,519,223.74", "$390,096,370.86")
    answer_els = [x for x in md if any(fig in x for fig in figures)]
    assert answer_els, "answer figures not found in rendered markdown"
    for el in answer_els:
        assert "`" not in el, f"code span survived in: {el[:120]!r}"
        assert "\\" not in el, f"backslash escape leaked in: {el[:120]!r}"
    page_text = " ".join(md)
    assert page_text.count("28.86") >= 2  # both occurrences, plain, everywhere
    assert "13,519,223.74" in page_text
    assert "$390,096,370.86" in page_text


def test_toggle_label_is_plain_text_without_icon(seeded_db):
    """Item 2 regression: the collapsible must be a clean "Show full answer"
    text label. The old icon=:material/unfold_more: leaked as literal
    ligature text (stExpanderIcon isn't covered by the theme's material-font
    override), visually overlapping the label."""
    at = _run_history()
    expanders = at.expander
    assert len(expanders) == len(seeded_db)
    for ex in expanders:
        assert ex.label == "Show full answer"
        # No custom icon is set on the expander anymore.
        assert ex.icon == ""
    # Nothing anywhere on the page carries the old icon request or its leaked
    # ligature text (the CSS *rule* mentioning stExpanderIcon is intentional).
    page_text = " ".join(_all_markdown(at))
    assert "unfold_more" not in page_text
    # The full answers are still reachable inside each expander.
    for _key, _cid, answer in seeded_db:
        assert answer.rstrip() in " ".join(_all_markdown(at))