"""Tests for the SQL safety validator — the hard security boundary."""
import pytest

from agents.sql_agent.validator import (
    SQLValidationError,
    validate_sql,
    FORBIDDEN_KEYWORDS,
)


class TestValidateSql:
    def test_accepts_simple_select(self):
        out = validate_sql("SELECT * FROM Orders")
        assert out.startswith("SELECT")

    def test_adds_default_row_limit(self):
        out = validate_sql("SELECT * FROM Orders")
        assert "LIMIT" in out.upper()

    def test_keeps_existing_limit(self):
        out = validate_sql("SELECT * FROM Orders LIMIT 5")
        assert out.upper().endswith("LIMIT 5")

    def test_strips_comments(self):
        out = validate_sql("SELECT * FROM Orders -- comment\n/* block */")
        assert "comment" not in out
        assert out.startswith("SELECT")

    def test_allows_single_trailing_semicolon(self):
        out = validate_sql("SELECT * FROM Orders;")
        assert "LIMIT" in out.upper()

    def test_rejects_non_select(self):
        with pytest.raises(SQLValidationError):
            validate_sql("DROP TABLE Orders")

    def test_rejects_statement_chaining(self):
        with pytest.raises(SQLValidationError):
            validate_sql("SELECT * FROM Orders; DROP TABLE Orders")

    @pytest.mark.parametrize("keyword", FORBIDDEN_KEYWORDS)
    def test_rejects_forbidden_keywords(self, keyword):
        with pytest.raises(SQLValidationError):
            validate_sql(f"SELECT * FROM Orders {keyword}")

    def test_rejects_empty(self):
        with pytest.raises(SQLValidationError):
            validate_sql("   -- just a comment  ")