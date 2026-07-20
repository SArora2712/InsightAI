"""
Reranking module for InsightAI.

Hybrid search (dense + sparse + RRF) is good at narrowing thousands of
chunks down to a shortlist, but it scores the query and each chunk
*independently* then compares vectors — it never actually reads them
together. A cross-encoder reranker does: it takes (query, chunk) as a
single joint input and outputs a relevance score directly. This catches
ranking mistakes hybrid search alone misses, especially on close calls.

Standard pattern: hybrid search retrieves a shortlist (e.g. top 20),
the reranker re-scores just that shortlist (cross-encoders are too slow
to run over an entire collection), and you keep the top N after rerank
(e.g. top 5) to actually pass to the LLM.


"""

from typing import List, Tuple

from ingestion.sparse import word_tokenize

_cross_encoder = None
_USING_CROSS_ENCODER = False


def _try_load_cross_encoder():
    global _cross_encoder, _USING_CROSS_ENCODER
    try:
        from fastembed.rerank.cross_encoder import TextCrossEncoder
        _cross_encoder = TextCrossEncoder(model_name="Xenova/ms-marco-MiniLM-L-6-v2")
        _USING_CROSS_ENCODER = True
        print("[reranker] Using fastembed cross-encoder (Xenova/ms-marco-MiniLM-L-6-v2) — real reranking.")
    except Exception as e:
        _USING_CROSS_ENCODER = False
        print(f"[reranker] Cross-encoder unavailable ({type(e).__name__}), falling back to lexical-overlap "
              f"reranking. Expected in network-restricted sandboxes; on your machine with normal internet "
              f"access, the real cross-encoder downloads once and this fallback won't trigger.")


_try_load_cross_encoder()


def _lexical_overlap_score(query: str, text: str) -> float:
    """Fallback reranker: Jaccard-style overlap between query and chunk
    tokens, weighted slightly toward query coverage (how much of the query
    is addressed) since that matters more than chunk brevity."""
    q_tokens = set(word_tokenize(query))
    t_tokens = set(word_tokenize(text))
    if not q_tokens or not t_tokens:
        return 0.0
    overlap = q_tokens & t_tokens
    query_coverage = len(overlap) / len(q_tokens)
    jaccard = len(overlap) / len(q_tokens | t_tokens)
    return 0.7 * query_coverage + 0.3 * jaccard


def rerank(query: str, candidates: List[Tuple[str, str]], top_n: int = 5) -> List[Tuple[str, str, float]]:
    """Re-score a shortlist of (id, text) candidates against the query.
    Returns (id, text, score) sorted best-first, truncated to top_n."""
    if not candidates:
        return []

    ids, texts = zip(*candidates)

    if _USING_CROSS_ENCODER:
        scores = list(_cross_encoder.rerank(query, list(texts)))
    else:
        scores = [_lexical_overlap_score(query, t) for t in texts]

    scored = list(zip(ids, texts, scores))
    scored.sort(key=lambda x: x[2], reverse=True)
    return scored[:top_n]


if __name__ == "__main__":
    from ingestion.parser import parse_directory
    from ingestion.chunker import chunk_document
    from ingestion.embeddings import embed_texts, fit_fallback_vectorizer, _USING_FASTEMBED
    from ingestion.sparse import BM25Index
    from ingestion.vector_store import (
        get_client, ensure_collection, upsert_chunks, hybrid_search,
    )

    docs = parse_directory("data/raw")
    all_chunks = []
    for d in docs:
        all_chunks.extend(chunk_document(d, chunk_size=120, chunk_overlap=20))
    texts = [c.text for c in all_chunks]

    if not _USING_FASTEMBED:
        fit_fallback_vectorizer(texts)
    dense_vectors = embed_texts(texts)

    bm25 = BM25Index()
    bm25.fit(texts)
    sparse_vectors = [bm25.encode(t) for t in texts]

    client = get_client()
    ensure_collection(client)
    upsert_chunks(client, all_chunks, dense_vectors, sparse_vectors)

    query = "What is driving customer churn and what caused it?"
    q_dense = embed_texts([query])[0]
    q_sparse = bm25.encode(query)

    # Stage 1: hybrid search gets a shortlist (e.g. top 10)
    hybrid_results = hybrid_search(client, q_dense, q_sparse, limit=10)
    print(f"Query: '{query}'")
    print(f"\nStage 1 — hybrid search shortlist ({len(hybrid_results)} candidates):")
    for r in hybrid_results:
        print(f"  rrf_score={r.score:.4f}  [{r.payload['chunk_id']}]  {r.payload['text'][:80]}...")

    # Stage 2: reranker re-scores just that shortlist
    candidates = [(r.payload["chunk_id"], r.payload["text"]) for r in hybrid_results]
    reranked = rerank(query, candidates, top_n=5)

    print(f"\nStage 2 — reranked top 5 (using {'real cross-encoder' if _USING_CROSS_ENCODER else 'lexical-overlap fallback'}):")
    for chunk_id, text, score in reranked:
        print(f"  rerank_score={score:.4f}  [{chunk_id}]  {text[:80]}...")

    client.close()