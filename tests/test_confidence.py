"""Tests for the rule-based confidence scorer."""
from agents.orchestrator.confidence import compute_confidence


def _empty_rag():
    return {"retrieved_chunks": [], "answer": ""}


def _good_rag():
    return {"retrieved_chunks": [{"score": 0.9}], "answer": "ok"}


def _empty_sql():
    return {"row_count": 0, "error": None, "attempts": 1}


def _good_sql():
    return {"row_count": 5, "error": None, "attempts": 1}


def _no_sources():
    return (None, None, None)


class TestComputeConfidence:
    def test_no_sources_is_zero(self):
        result = compute_confidence(False, *_no_sources())
        assert result["score"] == 0.0
        assert result["label"] == "Low"

    def test_conflict_penalizes_heavily(self):
        result = compute_confidence(True, _good_rag(), _good_sql(), None)
        assert result["score"] <= 0.55
        assert "disagree" in " ".join(result["reasons"]).lower()

    def test_single_source_reduces_score(self):
        base = compute_confidence(False, _good_rag(), _good_sql(), None)
        single = compute_confidence(False, _good_rag(), None, None)
        assert single["score"] < base["score"]

    def test_sql_error_penalized(self):
        rag = _good_rag()
        bad_sql = {"row_count": 0, "error": "boom", "attempts": 3}
        result = compute_confidence(False, rag, bad_sql, None)
        assert "SQL" in " ".join(result["reasons"])

    def test_high_score_label(self):
        result = compute_confidence(False, _good_rag(), _good_sql(), None)
        assert result["label"] in ("High", "Medium")
        assert 0.0 <= result["score"] <= 1.0

    def test_deterministic_same_inputs(self):
        a = compute_confidence(False, _good_rag(), _good_sql(), None)
        b = compute_confidence(False, _good_rag(), _good_sql(), None)
        assert a == b