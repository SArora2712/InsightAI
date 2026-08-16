"""Unit tests for the stopgap auth gate (core.auth).

The gate is NOT production auth; these tests lock in the stopgap contract:
single shared credential from env, session flag set only on success, and the
admin check requiring both auth and the configured username.
"""
from types import SimpleNamespace

import pytest

import core.auth as auth


@pytest.fixture()
def fake_session(monkeypatch):
    """Swap streamlit for a stub so session_state acts like a plain dict."""
    session = {"authenticated": False, "username": None}
    monkeypatch.setattr(auth, "st", SimpleNamespace(session_state=session))
    return session


def test_default_credentials(monkeypatch):
    monkeypatch.delenv("APP_USERNAME", raising=False)
    monkeypatch.delenv("APP_PASSWORD", raising=False)
    assert auth.expected_username() == "admin"
    assert auth.expected_password() == "insightai"


def test_env_credentials_override_defaults(monkeypatch):
    monkeypatch.setenv("APP_USERNAME", "boss")
    monkeypatch.setenv("APP_PASSWORD", "hunter2")
    assert auth.expected_username() == "boss"
    assert auth.expected_password() == "hunter2"


def test_authenticate_success_sets_admin_role(fake_session, monkeypatch):
    monkeypatch.setenv("APP_USERNAME", "admin")
    monkeypatch.setenv("APP_PASSWORD", "insightai")
    assert auth.authenticate("admin", "insightai") is True
    assert fake_session["authenticated"] is True
    assert fake_session["username"] == "admin"
    assert fake_session["role"] == "admin"


def test_authenticate_wrong_password_fails(fake_session, monkeypatch):
    monkeypatch.setenv("APP_USERNAME", "admin")
    monkeypatch.setenv("APP_PASSWORD", "insightai")
    assert auth.authenticate("admin", "wrong") is False
    assert fake_session["authenticated"] is False


def test_login_as_guest_sets_guest_role(fake_session):
    auth.login_as_guest()
    assert fake_session["authenticated"] is True
    assert fake_session["role"] == "guest"
    assert fake_session["username"] == "guest"


def test_not_authenticated_by_default(fake_session):
    assert auth.is_authenticated() is False


def test_is_admin_requires_admin_role(fake_session, monkeypatch):
    monkeypatch.setenv("APP_USERNAME", "admin")
    assert auth.is_admin() is False
    fake_session["authenticated"] = True
    fake_session["role"] = "guest"
    assert auth.is_admin() is False
    fake_session["role"] = "admin"
    assert auth.is_admin() is True


def test_guest_is_not_admin(fake_session):
    auth.login_as_guest()
    assert auth.is_authenticated() is True
    assert auth.is_admin() is False


def test_logout_clears_flags(fake_session, monkeypatch):
    monkeypatch.setenv("APP_USERNAME", "admin")
    monkeypatch.setenv("APP_PASSWORD", "insightai")
    auth.authenticate("admin", "insightai")
    auth.logout()
    assert fake_session.get("authenticated") is None
    assert "username" not in fake_session
    assert "role" not in fake_session