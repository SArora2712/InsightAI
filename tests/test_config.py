"""Tests for the centralized, unified chunking configuration (C2)."""
from ingestion.config import CHUNK_SIZE, CHUNK_OVERLAP


class TestUnifiedChunkConfig:
    def test_chunk_size_default(self):
        # All entry points (setup.py, api/main.py, eval) read from config,
        # so the default MUST be uniform here. 120/20 is the canonical value.
        assert CHUNK_SIZE == 120
        assert CHUNK_OVERLAP == 20

    def test_overlap_smaller_than_size(self):
        assert CHUNK_OVERLAP < CHUNK_SIZE
        assert CHUNK_OVERLAP >= 0