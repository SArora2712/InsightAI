"""AppTest tests for chat branding (Fix 3 + regression guard).

The large "InsightAI" heading + tagline must only appear on the empty chat
state. Once a conversation exists, only the small icon+wordmark header is
shown. The header icon must be the single-source favicon mark (viewBox 96),
and the wordmark must appear exactly once (never baked-into-the-svg twice).

Note: the Qdrant lock on this machine stops the chat page after the hero block,
so these tests assert on the hero markup itself (rendered before setup).
"""
from pathlib import Path

from streamlit.testing.v1 import AppTest

CHAT_PY = str(Path(__file__).resolve().parents[1] / "chat2.py")


def _chat_at(messages):
    at = AppTest.from_file(CHAT_PY, default_timeout=120)
    at.session_state["authenticated"] = True
    at.session_state["role"] = "admin"
    at.session_state["username"] = "admin"
    at.session_state["messages"] = messages
    at.session_state["conversation_id"] = None
    at.run()
    return at


def _hero_html(at) -> str:
    return " ".join(m.value for m in at.markdown)


LARGE = "class='ia-hero'"
COMPACT = "class='ia-hero ia-hero--compact'"
TAGLINE = "What would you like to analyze?"
FAVICON_MARK = 'viewBox="0 0 96 96"'
# logo.svg bakes a <text> wordmark into the image; rendering it in the hero
# duplicates the heading. This must never appear in the chat hero.
SVG_WORDMARK = "<text "


def test_empty_state_shows_large_heading_with_tagline():
    at = _chat_at([])
    html = _hero_html(at)
    assert LARGE in html
    assert TAGLINE in html
    assert COMPACT not in html
    assert SVG_WORDMARK not in html
    assert FAVICON_MARK in html


def test_active_chat_hides_large_heading():
    at = _chat_at(
        [
            {"role": "user", "content": "Hello", "meta": None},
            {"role": "assistant", "content": "Hi! How can I help?", "meta": {}},
        ]
    )
    html = _hero_html(at)
    # Large heading (with tagline) is gone once a message exists.
    assert LARGE not in html
    assert TAGLINE not in html
    # The small icon+wordmark header remains, with the favicon-based mark only.
    assert COMPACT in html
    assert "ia-hero-name" in html
    assert FAVICON_MARK in html
    assert SVG_WORDMARK not in html