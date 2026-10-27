"""
Orchestrator graph integration test (marked `integration`).

Builds the real index and runs the full Workflow (v1) graph on a few
questions. Without an LLM key the model returns the documented no-key
placeholder, so assertions focus on graph wiring (state shape), not on
answer content.
"""
import pytest

from ingestion.parser import parse_directory
from ingestion.chunker import chunk_document
from ingestion.vector_store import VectorStore
from ingestion.sparse import BM25Index
from ingestion.embeddings import get_provider
from ingestion.config import CHUNK_SIZE, CHUNK_OVERLAP
from agents.orchestrator.graph import build_orchestrator_graph


@pytest.mark.integration
def test_workflow_graph_returns_full_state():
    docs = parse_directory("data/raw")
    all_chunks = []
    for d in docs:
        all_chunks.extend(chunk_document(d, chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP))
    texts = [c.text for c in all_chunks]

    provider = get_provider()
    provider.fit_if_needed(texts)
    dense = provider.embed_texts(texts)

    bm25 = BM25Index()
    bm25.fit(texts)
    sparse = [bm25.encode(t) for t in texts]

    store = VectorStore.get_instance()
    store.upsert_chunks(all_chunks, dense, sparse)
    app = build_orchestrator_graph(bm25, provider, store.client)

    result = app.invoke({
        "query": "What was total revenue by category last quarter?",
        "agents_needed": [], "rag_result": None, "sql_result": None,
        "web_result": None, "final_answer": None, "conflict_detected": None,
        "conflict_summary": None, "confidence": None, "critique": None,
    })

    assert "final_answer" in result
    assert isinstance(result["agents_needed"], list)
    store.close()


if __name__ == "__main__":
    import sys
    sys.exit(pytest.main([__file__, "-m", "integration"]))