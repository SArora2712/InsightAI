"""
Day 6 — Retrieval evaluation.

A small, hand-written test set of (query, expected_doc, expected_page)
triples, checked against what the pipeline actually retrieves. This is
NOT RAGAS (that's Week 3, once generation is wired up with a real LLM
answer to evaluate) — this is a much simpler, honest sanity check:
does hybrid search + rerank actually put the RIGHT chunk on top?

Run this any time you change chunk size, embedding model, or reranking
logic — it's the fastest way to catch a retrieval regression before it
shows up as a wrong answer three stages later.
"""

from dataclasses import dataclass
from typing import List

from ingestion.parser import parse_directory
from ingestion.chunker import chunk_document
from ingestion.embeddings import get_provider
from ingestion.sparse import fit_or_load
from ingestion.vector_store import VectorStore
from ingestion.reranker import rerank


@dataclass
class TestCase:
    query: str
    expected_doc: str
    expected_page: int  # accept the top-1 result if it comes from this page
    note: str = ""


# Edit this list to match whatever documents you're actually testing against.
TEST_SET: List[TestCase] = [
    TestCase(
        query="What is driving customer churn and what caused it?",
        expected_doc="q3_sales_report",
        expected_page=3,
        note="Risks and Watch Items section",
    ),
    TestCase(
        query="What was the ROAS on the marketing campaigns?",
        expected_doc="q3_sales_report",
        expected_page=2,
        note="Marketing Spend Analysis section — exact-term (ROAS) test",
    ),
    TestCase(
        query="How much revenue did the company make in Q3?",
        expected_doc="q3_sales_report",
        expected_page=1,
        note="Executive Summary — should not be pulled off by later pages",
    ),
    TestCase(
        query="What is the Q4 revenue target?",
        expected_doc="q3_sales_report",
        expected_page=3,
        note="Q4 Outlook section",
    ),
]


def run_evaluation(test_set: List[TestCase] = TEST_SET, top_k: int = 3):
    docs = parse_directory("data/raw")
    all_chunks = []
    for d in docs:
        all_chunks.extend(chunk_document(d, chunk_size=120, chunk_overlap=20))
    texts = [c.text for c in all_chunks]

    provider = get_provider()
    provider.fit_if_needed(texts)
    dense_vectors = provider.embed_texts(texts)

    bm25 = fit_or_load(texts, force_refit=True)
    sparse_vectors = [bm25.encode(t) for t in texts]

    store = VectorStore.get_instance()
    store.upsert_chunks(all_chunks, dense_vectors, sparse_vectors)

    print(f"\n{'='*70}")
    print(f"Running {len(test_set)} test cases against {len(all_chunks)} chunks "
          f"from {len(docs)} document(s)")
    print(f"{'='*70}\n")

    passed = 0
    for i, case in enumerate(test_set, 1):
        q_dense = provider.embed_texts([case.query])[0]
        q_sparse = bm25.encode(case.query)

        hybrid_results = store.hybrid_search(q_dense, q_sparse, limit=10)
        candidates = [(r.payload["chunk_id"], r.payload["text"]) for r in hybrid_results]
        payload_by_id = {r.payload["chunk_id"]: r.payload for r in hybrid_results}
        reranked = rerank(case.query, candidates, top_n=top_k)

        if not reranked:
            print(f"[{i}] FAIL — no results at all — '{case.query}'")
            continue

        top_chunk_id = reranked[0][0]
        top_payload = payload_by_id[top_chunk_id]
        got_doc = top_payload["doc_name"]
        got_page = top_payload["page_number"]

        ok = (got_doc == case.expected_doc and got_page == case.expected_page)
        status = "PASS" if ok else "FAIL"
        if ok:
            passed += 1

        print(f"[{i}] {status} — '{case.query}'")
        print(f"     expected: {case.expected_doc} page {case.expected_page}  ({case.note})")
        print(f"     got:      {got_doc} page {got_page}")
        if not ok:
            print(f"     top-{top_k} candidates were:")
            for cid, text, score in reranked:
                p = payload_by_id[cid]
                print(f"       - {p['doc_name']} page {p['page_number']}  score={score:.3f}  {text[:60]}...")
        print()

    print(f"{'='*70}")
    print(f"Result: {passed}/{len(test_set)} passed ({100*passed/len(test_set):.0f}%)")
    print(f"{'='*70}\n")

    if passed < len(test_set):
        print("Failures are useful signal, not a red flag by themselves — check whether:")
        print("  - the expected page is genuinely wrong (fix the test case), or")
        print("  - chunk_size/overlap is splitting relevant content awkwardly, or")
        print("  - the reranker fallback (lexical overlap) is weaker than a real")
        print("    cross-encoder would be here — worth rechecking once you're running")
        print("    with the real fastembed reranker on your machine.")

    return passed, len(test_set)


if __name__ == "__main__":
    run_evaluation()