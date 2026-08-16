"""
Centralized configuration for InsightAI's ingestion pipeline.


"""

import os

from core.envutil import read_env, read_env_int

# --- Chunking ---
# Single source of truth for chunking parameters. All entry points
# (core/setup.py, api/main.py, eval scripts, rag_agent __main__) read from
# here instead of hardcoding values, so a change cannot silently create a
# stale index. If you change these, the vector index is rebuilt automatically
# (see core/setup.py's config-keyed cache).
CHUNK_SIZE = read_env_int("CHUNK_SIZE", 120)
CHUNK_OVERLAP = read_env_int("CHUNK_OVERLAP", 20)

# --- Dense embeddings ---
EMBEDDING_DIM = read_env_int("EMBEDDING_DIM", 384)
DENSE_MODEL_NAME = read_env("DENSE_MODEL_NAME", "BAAI/bge-small-en-v1.5")
EMBEDDING_BATCH_SIZE = read_env_int("EMBEDDING_BATCH_SIZE", 32)

# --- Sparse / BM25 ---
BM25_K1 = float(read_env("BM25_K1", "1.5"))
BM25_B = float(read_env("BM25_B", "0.75"))
BM25_INDEX_PATH = read_env("BM25_INDEX_PATH", "./data/bm25_index.json")

# --- Vector store ---
QDRANT_COLLECTION = read_env("QDRANT_COLLECTION", "insightai_docs")
QDRANT_LOCAL_PATH = read_env("QDRANT_LOCAL_PATH", "./data/qdrant_local")
QDRANT_URL = read_env("QDRANT_URL", "")
QDRANT_API_KEY = read_env("QDRANT_API_KEY", "")
UPSERT_BATCH_SIZE = read_env_int("UPSERT_BATCH_SIZE", 100)

# --- Retrieval ---
HYBRID_SEARCH_LIMIT = read_env_int("HYBRID_SEARCH_LIMIT", 10)
RERANK_TOP_N = read_env_int("RERANK_TOP_N", 5)
CROSS_ENCODER_MODEL = read_env("CROSS_ENCODER_MODEL", "Xenova/ms-marco-MiniLM-L-6-v2")