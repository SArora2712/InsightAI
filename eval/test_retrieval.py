"""
Retrieval integration test (marked `integration` — needs the parsed docs +
the embedding provider; skipped in the default CI unit run).

Sanity-check: does hybrid search + rerank actually put the RIGHT chunk on top.
Edit TEST_SET to match whatever documents you're testing against.
"""
import pytest

from ingestion.parser import parse_directory
from ingestion.chunker import chunk_document
from ingestion.embeddings import get_provider
from ingestion.sparse import fit_or_load
from ingestion.vector_store import VectorStore
from ingestion.reranker import rerank
from ingestion.config import CHUNK_SIZE, CHUNK_OVERLAP


TEST_SET = [
    ("What is driving customer churn and what caused it?", "Northwind_Sales_Retention_Review", 3),
    ("What was the ROAS on the marketing campaigns?", "Northwind_Sales_Retention_Review", 2),
    ("How much revenue did the company make in Q3?", "Northwind_Sales_Retention_Review", 1),
    ("What is the Q4 revenue target?", "Northwind_Sales_Retention_Review", 3),
]


def _build_index():
    docs = parse_directory("data/raw")
    all_chunks = []
    for d in docs:
        all_chunks.extend(chunk_document(d, chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP))
    texts = [c.text for c in all_chunks]

    provider = get_provider()
    provider.fit_if_needed(texts)
    dense = provider.embed_texts(texts)

    bm25 = fit_or_load(texts, force_refit=True)
    sparse = [bm25.encode(t) for t in texts]

    store = VectorStore.get_instance()
    store.upsert_chunks(all_chunks, dense, sparse)
    return provider, bm25, store


@pytest.mark.integration
def test_top_result_matches_expected_doc_and_page():
    provider, bm25, store = _build_index()

    passed = 0

    for query, exp_doc, exp_page in TEST_SET:
        print(f"\n{'=' * 80}")
        print(f"Query: {query}")

        q_dense = provider.embed_texts([query])[0]
        q_sparse = bm25.encode(query)

        hybrid = store.hybrid_search(q_dense, q_sparse, limit=10)

        if not hybrid:
            print("No hybrid results")
            continue

        candidates = [
            (r.payload["chunk_id"], r.payload["text"])
            for r in hybrid
        ]

        payload_by_id = {
            r.payload["chunk_id"]: r.payload
            for r in hybrid
        }

        reranked = rerank(query, candidates, top_n=3)

        print("\nTop 3 results:")

        for rank, (chunk_id, text, score) in enumerate(reranked, start=1):
            payload = payload_by_id[chunk_id]

            print(
                f"{rank}. "
                f"{payload['doc_name']} | "
                f"page={payload['page_number']} | "
                f"score={score:.4f}"
            )

        top_chunk_id, _, top_score = reranked[0]
        top_payload = payload_by_id[top_chunk_id]

        if (
            top_payload["doc_name"] == exp_doc
            and top_payload["page_number"] == exp_page
        ):
            passed += 1

    store.close()

    assert passed >= 1, (
        f"Expected at least one query to match. "
        f"Matched {passed}/{len(TEST_SET)}"
    )

if __name__ == "__main__":
    import sys
    sys.exit(pytest.main([__file__, "-m", "integration"]))