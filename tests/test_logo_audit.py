"""Logo audit (Item 5): exactly ONE in-page logo must render on every page.

Two logo renderers exist: app_logo_svg() (full logo.svg lockup, signature
viewBox 0 0 456 112, used where a self-contained logo is needed) and
small_logo_html() (icon + wordmark, header lockups, signature viewBox 0 0 96 96).
Chat + login heroes render the single-source favicon mark (favicon_mark_svg,
viewBox 0 0 96 96) which is the same art as small_logo_html. A page "shows a
logo" when exactly one of those signatures appears in its rendered markdown.
"""
import tempfile
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from core import history as history_mod

ROOT = Path(__file__).resolve().parents[1]
LOGIN_PY = str(ROOT / "app.py")
CHAT_PY = str(ROOT / "chat2.py")
DASHBOARD_PY = str(ROOT / "pages2" / "dashboard.py")
EXECUTIVE_PY = str(ROOT / "pages2" / "executive_report.py")
HISTORY_PY = str(ROOT / "pages2" / "history.py")
SIMULATOR_PY = str(ROOT / "pages2" / "simulator.py")
PERFORMANCE_PY = str(ROOT / "pages2" / "performance_monitor.py")

FULL_LOGO = 'viewBox="0 0 456 112"'          # app_logo_svg / logo.svg
SMALL_LOGO = 'viewBox="0 0 96 96"'           # small_logo_html


def _logo_count(at) -> int:
    text = " ".join(m.value for m in at.markdown)
    return text.count(FULL_LOGO) + text.count(SMALL_LOGO)


def _auth(at):
    at.session_state["authenticated"] = True
    at.session_state["role"] = "admin"
    at.session_state["username"] = "admin"


def test_login_page_shows_exactly_one_logo():
    at = AppTest.from_file(LOGIN_PY, default_timeout=120)
    at.run()
    assert not at.exception
    assert _logo_count(at) == 1


def test_chat_empty_state_shows_exactly_one_logo():
    at = AppTest.from_file(CHAT_PY, default_timeout=120)
    _auth(at)
    at.session_state["conversation_id"] = None
    at.session_state["messages"] = []
    at.run()
    assert not at.exception
    assert _logo_count(at) == 1


def test_chat_active_thread_shows_exactly_one_logo():
    at = AppTest.from_file(CHAT_PY, default_timeout=120)
    _auth(at)
    at.session_state["conversation_id"] = None
    at.session_state["messages"] = [
        {"role": "user", "content": "Hello", "meta": None},
        {"role": "assistant", "content": "Hi!", "meta": {}, "processing_steps": []},
    ]
    at.run()
    assert not at.exception
    assert _logo_count(at) == 1


def test_dashboard_shows_exactly_one_logo():
    at = AppTest.from_file(DASHBOARD_PY, default_timeout=120)
    _auth(at)
    at.run()
    assert not at.exception
    assert _logo_count(at) == 1


def test_executive_report_shows_exactly_one_logo():
    at = AppTest.from_file(EXECUTIVE_PY, default_timeout=120)
    _auth(at)
    at.session_state["executive_report"] = None
    at.run()
    assert not at.exception
    assert _logo_count(at) == 1


def test_history_shows_exactly_one_logo(monkeypatch):
    monkeypatch.setattr(history_mod, "DB_PATH", Path(tempfile.mkdtemp()) / "history.db")
    history_mod.init_db()
    cid = history_mod.create_conversation()
    history_mod.maybe_set_title_from_first_message(cid, "Q")
    history_mod.save_message(cid, "user", "Q")
    history_mod.save_message(cid, "assistant", "A")

    at = AppTest.from_file(HISTORY_PY, default_timeout=120)
    _auth(at)
    at.run()
    assert not at.exception
    assert _logo_count(at) == 1


def test_simulator_shows_exactly_one_logo():
    at = AppTest.from_file(SIMULATOR_PY, default_timeout=120)
    _auth(at)
    at.session_state["simulator_history"] = []
    at.run()
    assert not at.exception
    assert _logo_count(at) == 1


def test_performance_monitor_shows_exactly_one_logo_for_admin():
    at = AppTest.from_file(PERFORMANCE_PY, default_timeout=120)
    _auth(at)
    at.run()
    assert not at.exception
    assert _logo_count(at) == 1


def test_performance_monitor_shows_exactly_one_logo_for_guest():
    at = AppTest.from_file(PERFORMANCE_PY, default_timeout=120)
    at.session_state["authenticated"] = True
    at.session_state["role"] = "guest"
    at.session_state["username"] = "guest"
    at.run()
    assert not at.exception
    assert _logo_count(at) == 1


@pytest.mark.parametrize(
    "path, seeded_state",
    [
        (LOGIN_PY, {}),
        (DASHBOARD_PY, {}),
        (EXECUTIVE_PY, {"executive_report": None}),
        (SIMULATOR_PY, {"simulator_history": []}),
        (PERFORMANCE_PY, {}),
    ],
)
def test_no_page_renders_more_than_one_logo(path, seeded_state):
    """Every app page must render AT MOST one logo (the exact-one pages above
    assert exactly-one; this adds a hard ceiling check on the shared ones)."""
    at = AppTest.from_file(path, default_timeout=120)
    _auth(at)
    for k, v in seeded_state.items():
        at.session_state[k] = v
    at.run()
    assert not at.exception
    assert _logo_count(at) <= 1