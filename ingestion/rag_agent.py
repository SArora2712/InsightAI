"""
Document RAG Agent — Day 5.

"""

import os
from typing import TypedDict, List, Optional

from dotenv import load_dotenv
load_dotenv()

from ingestion.vector_store import get_client, ensure_collection, hybrid_search
from ingestion.reranker import rerank
from ingestion.embeddings import get_provider, EmbeddingProvider
from ingestion.sparse import BM25Index


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

import time
import openai  # add if not already imported

def generate_answer(query: str, chunks: List[dict]) -> str:
    api_key = os.getenv("LLM_API_KEY", "")
    if not api_key:
        return ("[No LLM_API_KEY set — skipping generation. "
                "Retrieval + prompt construction above are already verified; "
                "add your key to .env to see the actual generated answer.]")

    from openai import OpenAI
    client = OpenAI(
        base_url=os.getenv("LLM_BASE_URL", "https://api.groq.com/openai/v1"),
        api_key=api_key,
    )
    model = os.getenv("LLM_MODEL", "llama-3.3-70b-versatile")
    prompt = build_prompt(query, chunks)

    for attempt in range(3):
        try:
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": prompt},
                ],
            )
            return response.choices[0].message.content
        except openai.RateLimitError as e:
            if attempt < 2:
                wait = 8 * (attempt + 1)  # 8s, then 16s
                print(f"[rag_agent] Rate limited, waiting {wait}s before retry {attempt + 1}/2...")
                time.sleep(wait)
            else:
                return "[Rate limit reached — could not generate an answer. Try again shortly.]"

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
        all_chunks.extend(chunk_document(d, chunk_size=120, chunk_overlap=20))
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
    print(f"Query: '{query}'\n")

    result = app.invoke({"query": query, "retrieved_chunks": [], "answer": ""})

    print(f"Retrieved {len(result['retrieved_chunks'])} chunks:")
    for c in result["retrieved_chunks"]:
        print(f"  [{c['chunk_id']}] score={c['score']:.4f}  {c['text'][:70]}...")

    print(f"\n--- Constructed prompt (what gets sent to the LLM) ---")
    print(build_prompt(query, result["retrieved_chunks"])[:600] + "...\n")

    print(f"--- Answer ---")
    print(result["answer"])
    client.close()