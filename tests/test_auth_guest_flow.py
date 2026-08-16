"""AppTest flow tests for the stopgap auth gate (Fix 1).

Verifies the three behaviors the guest-path ticket requires:
  1. A guest can reach the Chat page without any credentials (via the
     "Try the demo" entry button on the landing page).
  2. A guest session is blocked from the Performance Monitor page.
  3. An admin login (reached through the landing "Sign in" → auth view)
     still works and reaches the Performance Monitor.
"""
from pathlib import Path

from streamlit.testing.v1 import AppTest

REPO_ROOT = Path(__file__).resolve().parents[1]
APP_PY = str(REPO_ROOT / "app.py")
PERF_PY = str(REPO_ROOT / "pages2" / "performance_monitor.py")


def _new_app():
    return AppTest.from_file(APP_PY, default_timeout=180)


def _new_perf():
    return AppTest.from_file(PERF_PY, default_timeout=120)


def _open_auth(at):
    """From the landing page, click the nav "Sign in" to reach the auth view."""
    at.run()
    at.button(key="landing_signin_btn").click().run()


def test_landing_is_the_entry_point_not_the_login_form():
    at = _new_app()
    at.run()
    assert at.session_state["view"] == "landing"
    # Login inputs are not shown on the landing page; it is nav + hero only.
    assert len(at.text_input) == 0
    labels = {b.label for b in at.button}
    assert "Try the demo" in labels
    assert "Have an account? Sign in" in labels


def test_sign_in_reaches_login_view_with_guest_button():
    at = _new_app()
    _open_auth(at)
    assert at.session_state["view"] == "auth"
    assert len(at.text_input) == 2  # Username + Password
    labels = {b.label for b in at.button}
    assert "Sign in" in labels
    assert "Continue as Guest" in labels


def test_guest_flow_reaches_chat_without_credentials():
    at = _new_app()
    at.run()
    at.button(key="landing_demo_btn").click().run()
    assert at.session_state["authenticated"] is True
    assert at.session_state["role"] == "guest"
    assert at.session_state["view"] == "app"
    # No login form on the app; Chat renders its sidebar actions.
    assert len(at.text_input) == 0
    labels = {b.label for b in at.button}
    assert "New analysis" in labels
    assert "Clear chat" in labels


def _sign_in_button(at):
    return next(b for b in at.button if b.label == "Sign in")


def test_guest_blocked_from_performance_monitor():
    at = _new_perf()
    at.session_state["authenticated"] = True
    at.session_state["role"] = "guest"
    at.session_state["username"] = "guest"
    at.run()
    info_texts = " ".join(i.value for i in at.info)
    assert "Admin access required" in info_texts


def test_admin_login_flow_reaches_performance_monitor():
    at = _new_app()
    _open_auth(at)
    at.text_input(key="login_username").set_value("admin")
    at.text_input(key="login_password").set_value("insightai")
    _sign_in_button(at).click().run()
    assert at.session_state["authenticated"] is True
    assert at.session_state["role"] == "admin"
    assert at.session_state["view"] == "app"


def test_admin_renders_performance_monitor_page():
    at = _new_perf()
    at.session_state["authenticated"] = True
    at.session_state["role"] = "admin"
    at.session_state["username"] = "admin"
    at.run()
    assert not at.exception
    assert not any("Admin access required" in i.value for i in at.info)
    assert [t.value for t in at.title] == ["Performance monitor"]