"""
Agent v2 graph-loop integration test (marked `integration`).

Verifies the LangGraph agent loop returns a well-formed result for an
in-scope multi-tool question and the correct early return for an
out-of-scope question.
"""
import pytest

from ingestion.embeddings import get_provider
from ingestion.sparse import BM25Index
from ingestion.parser import parse_directory
from ingestion.chunker import chunk_document
from ingestion.vector_store import VectorStore
from ingestion.config import CHUNK_SIZE, CHUNK_OVERLAP

from agents.agentic.agent import build_agent_tools
from agents.agentic.graph_loop import run_agentic_query_v2


@pytest.mark.integration
def test_agent_v2_loop_shapes():
    docs = parse_directory("data/raw")
    all_chunks = []
    for d in docs:
        all_chunks.extend(chunk_document(d, chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP))
    texts = [c.text for c in all_chunks]

    provider = get_provider()
    provider.fit_if_needed(texts)
    bm25 = BM25Index()
    bm25.fit(texts)

    store = VectorStore.get_instance()
    tool_dispatch = build_agent_tools(bm25, provider, store.client)

    out_of_scope = run_agentic_query_v2("What is photosynthesis?", tool_dispatch)
    assert out_of_scope["iterations"] == 0
    assert out_of_scope["tool_calls_made"] == []

    in_scope = run_agentic_query_v2("What was total revenue by category?", tool_dispatch)
    assert "answer" in in_scope
    assert in_scope["iterations"] >= 0
    store.close()


if __name__ == "__main__":
    import sys
    sys.exit(pytest.main([__file__, "-m", "integration"]))