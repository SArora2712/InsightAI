"""Tests for the API bearer-token gate (I3)."""
import pytest
from fastapi import HTTPException

import api.main as api


class TestRequireToken:
    def test_open_when_token_unset(self, monkeypatch):
        monkeypatch.delenv("API_ACCESS_TOKEN", raising=False)
        api._API_TOKEN = (lambda: "")()
        assert api._require_token(None) is None  # no error raised

    def test_missing_header_raises_401(self, monkeypatch):
        api._API_TOKEN = "s3cret"
        with pytest.raises(HTTPException) as exc:
            api._require_token(None)
        assert exc.value.status_code == 401

    def test_wrong_token_raises_401(self, monkeypatch):
        api._API_TOKEN = "s3cret"
        with pytest.raises(HTTPException) as exc:
            api._require_token("Bearer wrong")
        assert exc.value.status_code == 401

    def test_correct_token_passes(self, monkeypatch):
        api._API_TOKEN = "s3cret"
        assert api._require_token("Bearer s3cret") is None