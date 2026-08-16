"""
Parity check between the manual agent loop and the LangGraph loop
(marked `integration`): both should agree that an out-of-scope question
takes zero iterations with no tool calls.
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
def test_out_of_scope_parity():
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

    result = run_agentic_query_v2("What is photosynthesis?", tool_dispatch)
    assert result["iterations"] == 0
    assert result["tool_calls_made"] == []
    store.close()


if __name__ == "__main__":
    import sys
    sys.exit(pytest.main([__file__, "-m", "integration"]))