"""
Document RAG Agent — Day 5.

"""

from typing import TypedDict, List, Optional

from ingestion.vector_store import get_client, ensure_collection, hybrid_search
from ingestion.reranker import rerank
from ingestion.embeddings import get_provider, EmbeddingProvider
from ingestion.sparse import BM25Index
from ingestion.config import CHUNK_SIZE, CHUNK_OVERLAP
from core.llm_client import call_llm
from core.logging_util import get_logger

logger = get_logger("ingestion.rag_agent")


# --- Retrieval ---------------------------------------------------------

def retrieve(
    query: str,
    bm25: BM25Index,
    provider: EmbeddingProvider,
    client=None,
    hybrid_limit: int = 10,
    rerank_top_n: int = 5,
) -> List[dict]:
    if client is None:
        client = get_client()
        ensure_collection(client)

    q_dense = provider.embed_texts([query])[0]   # <- was embed_texts([query])[0]
    q_sparse = bm25.encode(query)
    
    hybrid_results = hybrid_search(client, q_dense, q_sparse, limit=hybrid_limit)
    if not hybrid_results:
        return []

    candidates = [(r.payload["chunk_id"], r.payload["text"]) for r in hybrid_results]
    payload_by_id = {r.payload["chunk_id"]: r.payload for r in hybrid_results}

    reranked = rerank(query, candidates, top_n=rerank_top_n)

    return [
        {
            "chunk_id": chunk_id,
            "doc_name": payload_by_id[chunk_id]["doc_name"],
            "page_number": payload_by_id[chunk_id]["page_number"],
            "text": text,
            "score": score,
        }
        for chunk_id, text, score in reranked
    ]


# --- Prompt construction -------------------------------------------------

SYSTEM_PROMPT = """You are a business analyst assistant. Answer the user's question using ONLY \
the provided document excerpts. For every claim, cite the source using the format \
[doc_name, page N]. If the excerpts don't contain enough information to answer, say so \
explicitly rather than guessing."""


def build_prompt(query: str, chunks: List[dict]) -> str:
    context_blocks = []
    for c in chunks:
        context_blocks.append(f"[{c['doc_name']}, page {c['page_number']}]\n{c['text']}")
    context = "\n\n---\n\n".join(context_blocks)

    return f"""Document excerpts:

{context}

---

Question: {query}

Answer using only the excerpts above, with [doc_name, page N] citations for every claim."""


# --- Generation ------------------------------------------------------

def generate_answer(query: str, chunks: List[dict]) -> str:
    """
    Generate an answer using the shared LLM client (core/llm_client.py).
    The shared client owns API-key resolution, retries, rate limiting,
    and the per-query call budget — there is no separate OpenAI pathway
    here anymore.
    """
    if not chunks:
        return "[No relevant document excerpts were retrieved.]"

    prompt = build_prompt(query, chunks)
    try:
        return call_llm(SYSTEM_PROMPT, prompt)
    except Exception as e:
        return f"[Could not generate an answer ({type(e).__name__}: {e}).]"

# --- LangGraph node ----------------------------------------------------

class DocumentRAGState(TypedDict):
    query: str
    retrieved_chunks: List[dict]
    answer: str


def document_rag_node(state: DocumentRAGState, bm25: BM25Index, provider: EmbeddingProvider, client) -> DocumentRAGState:
    chunks = retrieve(state["query"], bm25, provider, client=client)
    answer = generate_answer(state["query"], chunks)
    return {"query": state["query"], "retrieved_chunks": chunks, "answer": answer}


def build_document_rag_graph(bm25: BM25Index, provider: EmbeddingProvider, client):
    from langgraph.graph import StateGraph, END
    graph = StateGraph(DocumentRAGState)
    graph.add_node("document_rag", lambda state: document_rag_node(state, bm25, provider, client))
    graph.set_entry_point("document_rag")
    graph.add_edge("document_rag", END)
    return graph.compile()


if __name__ == "__main__":
    from ingestion.parser import parse_directory
    from ingestion.chunker import chunk_document
    from ingestion.vector_store import upsert_chunks

    docs = parse_directory("data/raw")
    all_chunks = []
    for d in docs:
        all_chunks.extend(chunk_document(d, chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP))
    texts = [c.text for c in all_chunks]

    provider = get_provider()
    provider.fit_if_needed(texts)          # no-op for FastEmbedProvider; fits TF-IDF/SVD for the fallback
    dense_vectors = provider.embed_texts(texts)

    bm25 = BM25Index()
    bm25.fit(texts)
    sparse_vectors = [bm25.encode(t) for t in texts]

    client = get_client()
    ensure_collection(client)
    upsert_chunks(client, all_chunks, dense_vectors, sparse_vectors)

    app = build_document_rag_graph(bm25, provider, client)   # <- now 3 args, was 2
    
    query = "What is driving customer churn and what caused it?"
    logger.info("Query: %r", query)

    result = app.invoke({"query": query, "retrieved_chunks": [], "answer": ""})

    logger.info("Retrieved %s chunks:", len(result["retrieved_chunks"]))
    for c in result["retrieved_chunks"]:
        logger.info("  [%s] score=%.4f  %s...", c["chunk_id"], c["score"], c["text"][:70])

    logger.info("--- Constructed prompt (what gets sent to the LLM) ---")
    logger.info("%s...", build_prompt(query, result["retrieved_chunks"])[:600])

    logger.info("--- Answer ---")
    logger.info("%s", result["answer"])
    client.close()