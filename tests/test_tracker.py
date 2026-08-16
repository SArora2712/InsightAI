"""Tests for the LLM call/token tracker (I4 budget visibility)."""
from core.llm_client import LLMCallTracker


class TestLLMCallTracker:
    def test_reset_query_clears_query_counters(self):
        t = LLMCallTracker()
        t.record_call(100)
        t.record_call(50)
        t.reset_query()
        assert t.query_count == 0
        assert t.query_tokens == 0
        # session counters persist across resets
        assert t.session_total == 2
        assert t.session_tokens == 150

    def test_record_call_counts_and_tokens(self):
        t = LLMCallTracker()
        t.record_call(0)   # call without reported tokens still counts a call
        assert t.query_count == 1
        assert t.session_total == 1
        assert t.query_tokens == 0

    def test_snapshot_shape(self):
        t = LLMCallTracker()
        t.record_call(42)
        snap = t.snapshot()
        assert snap["query_count"] == 1
        assert snap["query_tokens"] == 42
        assert set(snap.keys()) == {
            "query_count", "session_total", "query_tokens", "session_tokens",
        }