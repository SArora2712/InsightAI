"""
P0-1 / P0-3 regression tests for Dashboard/History preview text.

- P0-1: preview snippets must not mangle "$" into the literal "\\$".
- P0-3: each Recent-insights card must bind to its own conversation's FIRST
        question answer - never show the identical final answer of a thread
        that drifted to a different topic.
"""
import tempfile
from pathlib import Path

from core import history


def _fresh_db():
    history.DB_PATH = Path(tempfile.mkdtemp()) / "history.db"
    history.init_db()


def _seed_conversation(title: str, pairs: list[tuple[str, str]]) -> str:
    cid = history.create_conversation()
    history.maybe_set_title_from_first_message(cid, pairs[0][0])
    for role, content in pairs:
        history.save_message(cid, role, content)
    return cid


def test_preview_snippet_does_not_mangle_dollar_sign():
    snippet = history.preview_snippet("Beverages at $92.2M, Condiments at $55.8M")
    assert "$92.2M" in snippet
    assert "$55.8M" in snippet
    assert "\\$" not in snippet


def test_preview_snippet_html_escapes_raw_tags():
    snippet = history.preview_snippet("<script>alert(1)</script>")
    assert "<script>" not in snippet
    assert "&lt;script&gt;" in snippet


def test_first_question_answer_binds_to_first_pair():
    messages = [
        {"role": "user", "content": "Is the revenue decline reflected in the data?"},
        {"role": "assistant", "content": "Yes, the decline is real."},
        {"role": "user", "content": "what was total revenue by category?"},
        {"role": "assistant", "content": "Beverages at $92.2M."},
    ]
    question, answer = history.first_question_answer(messages)
    assert question["content"].startswith("Is the revenue decline")
    assert "decline is real" in answer["content"]


def test_three_different_conversations_show_three_previews():
    _fresh_db()
    conversations = [
        (
            "What was total revenue by category?",
            [
                ("user", "What was total revenue by category?"),
                ("assistant", "Our total revenue by category: Beverages at $92.2M."),
                ("user", "which country has highest revenue?"),
                ("assistant", "The United States generates the highest revenue."),
            ],
        ),
        (
            "Is the revenue decline mentioned in our reports reflected in the data?",
            [
                ("user", "Is the revenue decline mentioned in our reports reflected in the data?"),
                ("assistant", "Yes, the revenue decline is reflected in the data."),
                ("user", "what was total revenue by category?"),
                ("assistant", "Our total revenue by category: Beverages at $92.2M."),
            ],
        ),
        (
            "How might current inflation affect future sales?",
            [
                ("user", "How might current inflation affect future sales?"),
                ("assistant", "Inflation may reduce discretionary demand for premium categories."),
            ],
        ),
    ]

    cids = [_seed_conversation(title, pairs) for title, pairs in conversations]

    previews = []
    for cid in cids:
        messages = history.load_conversation_messages(cid)
        _question, answer = history.first_question_answer(messages)
        assert answer is not None
        previews.append(history.preview_snippet(answer["content"]))

    # The three cards must show three distinct preview texts; the declined
    # and inflation cards must NOT be shadowed by the revenue answer.
    assert len(set(previews)) == 3
    assert "revenue decline is reflected" in previews[1]
    assert "Inflation may reduce" in previews[2]


def test_preview_ignores_empty_threads():
    _fresh_db()
    cid = history.create_conversation()  # no messages
    messages = history.load_conversation_messages(cid)
    question, answer = history.first_question_answer(messages)
    assert question is None and answer is None