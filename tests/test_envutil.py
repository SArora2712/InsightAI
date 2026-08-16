"""Tests for the shared env/secrets reader (st.secrets -> os.getenv fallback)."""
import os

from core.envutil import read_env, read_env_int


class TestReadEnv:
    def test_returns_env_value(self, monkeypatch):
        monkeypatch.setenv("INSIGHTAI_TEST_KEY", "abc")
        assert read_env("INSIGHTAI_TEST_KEY") == "abc"

    def test_returns_default_when_unset(self, monkeypatch):
        monkeypatch.delenv("INSIGHTAI_MISSING", raising=False)
        assert read_env("INSIGHTAI_MISSING", "fallback") == "fallback"

    def test_safe_outside_streamlit(self, monkeypatch):
        # Even with no secrets file / no streamlit session, this must not raise.
        monkeypatch.delenv("INSIGHTAI_OTHER", raising=False)
        assert read_env("INSIGHTAI_OTHER", "x") == "x"


class TestReadEnvInt:
    def test_parses_int(self, monkeypatch):
        monkeypatch.setenv("INSIGHTAI_NUM", "42")
        assert read_env_int("INSIGHTAI_NUM", 0) == 42

    def test_default_on_garbage(self, monkeypatch):
        monkeypatch.setenv("INSIGHTAI_NUM", "not-a-number")
        assert read_env_int("INSIGHTAI_NUM", 7) == 7

    def test_default_when_unset(self, monkeypatch):
        monkeypatch.delenv("INSIGHTAI_NUM", raising=False)
        assert read_env_int("INSIGHTAI_NUM", 9) == 9