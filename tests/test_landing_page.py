"""Landing page (pre-auth entry) view-state tests.

The app now boots into a landing view (nav + hero) instead of straight into
the login form. These tests lock in the view transitions:
    landing --right--> auth --right--> app   (Sign in)
    landing --right--> app                    (Try the demo / guest)
    auth    --right--> landing                (Back)
    app     --right--> landing                (Sign out)
The auth logic itself is untouched; only the wrapper deciding what renders
before authentication changes (core.landing / app.py routing).
"""
from pathlib import Path

from streamlit.testing.v1 import AppTest

REPO_ROOT = Path(__file__).resolve().parents[1]
APP_PY = str(REPO_ROOT / "app.py")


def _new_app():
    return AppTest.from_file(APP_PY, default_timeout=180)


def test_fresh_session_lands_on_landing_not_auth_not_app():
    at = _new_app()
    at.run()
    assert not at.exception
    assert at.session_state["view"] == "landing"
    assert "authenticated" not in at.session_state
    # Landing is nav + hero: hero CTA and tagline, no login inputs, no chat.
    assert len(at.text_input) == 0
    labels = {b.label for b in at.button}
    assert "Try the demo" in labels
    assert "Have an account? Sign in" in labels


def test_sign_in_button_transitions_to_auth_view():
    at = _new_app()
    at.run()
    at.button(key="landing_signin_btn").click().run()
    assert at.session_state["view"] == "auth"
    assert len(at.text_input) == 2  # existing login card: Username + Password
    labels = {b.label for b in at.button}
    assert "Sign in" in labels
    assert "Continue as Guest" in labels
    assert "Try the demo" not in labels


def test_try_the_demo_goes_straight_to_app_as_guest():
    at = _new_app()
    at.run()
    at.button(key="landing_demo_btn").click().run()
    assert at.session_state["view"] == "app"
    assert at.session_state["authenticated"] is True
    assert at.session_state["role"] == "guest"
    # No auth screen along the way: no username/password widgets on the app.
    assert len(at.text_input) == 0


def test_back_from_auth_returns_to_landing():
    at = _new_app()
    at.run()
    at.button(key="landing_signin_btn").click().run()
    assert at.session_state["view"] == "auth"
    at.button(key="auth_back_btn").click().run()
    assert at.session_state["view"] == "landing"
    assert "authenticated" not in at.session_state
    labels = {b.label for b in at.button}
    assert "Try the demo" in labels


def test_sign_out_returns_to_landing():
    at = _new_app()
    at.run()
    at.button(key="landing_demo_btn").click().run()
    assert at.session_state["view"] == "app"
    assert len(at.button) > 0
    at.button(key="sign_out_btn").click().run()
    assert "authenticated" not in at.session_state
    assert at.session_state["view"] == "landing"
    labels = {b.label for b in at.button}
    assert "Try the demo" in labels
    assert "Have an account? Sign in" in labels


def test_invalid_view_state_normalizes_back_to_landing():
    at = _new_app()
    at.session_state["view"] = "bogus"
    at.run()
    assert at.session_state["view"] == "landing"