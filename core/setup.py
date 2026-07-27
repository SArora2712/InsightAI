"""
InsightAI - Shared resource setup, cached once per process.
Imported by every page that needs the indexed data/agents, so no page
depends on another page having run first in the session.
"""
import streamlit as st

from ingestion.parser import parse_directory
from ingestion.chunker import chunk_document
from ingestion.vector_store import get_client, ensure_collection, upsert_chunks
from ingestion.sparse import BM25Index
from ingestion.embeddings import get_provider
from agents.orchestrator.graph import build_orchestrator_graph
from agents.agentic.agent import build_agent_tools


@st.cache_resource(show_spinner="Setting up InsightAI (indexing documents)...")
def setup_resources():
    print("\n[Setup] Ingesting documents and building indices...")

    docs = parse_directory("data/raw")
    if not docs:
        raise RuntimeError(
            "No documents were found in 'data/raw'. "
            "Please add your internal documents before starting InsightAI."
        )

    all_chunks = []
    for document in docs:
        all_chunks.extend(chunk_document(document, chunk_size=120, chunk_overlap=20))

    if not all_chunks:
        raise RuntimeError("Documents were found, but no chunks were generated.")

    texts = [chunk.text for chunk in all_chunks]
    provider = get_provider()
    provider.fit_if_needed(texts)
    dense_vectors = provider.embed_texts(texts)

    bm25 = BM25Index()
    bm25.fit(texts)
    sparse_vectors = [bm25.encode(text) for text in texts]

    client = get_client()
    ensure_collection(client)
    upsert_chunks(client, all_chunks, dense_vectors, sparse_vectors)

    workflow_app = build_orchestrator_graph(bm25, provider, client)
    agent_tools = build_agent_tools(bm25, provider, client)

    print(f"[Setup] Indexed {len(all_chunks)} chunks. Workflow and Agent modes ready.")
    return workflow_app, agent_tools, len(all_chunks)