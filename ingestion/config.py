"""
Centralized configuration for InsightAI's ingestion pipeline.


"""

import os

# --- Chunking ---
CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "300"))
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", "50"))

# --- Dense embeddings ---
EMBEDDING_DIM = int(os.getenv("EMBEDDING_DIM", "384"))
DENSE_MODEL_NAME = os.getenv("DENSE_MODEL_NAME", "BAAI/bge-small-en-v1.5")
EMBEDDING_BATCH_SIZE = int(os.getenv("EMBEDDING_BATCH_SIZE", "32"))

# --- Sparse / BM25 ---
BM25_K1 = float(os.getenv("BM25_K1", "1.5"))
BM25_B = float(os.getenv("BM25_B", "0.75"))
BM25_INDEX_PATH = os.getenv("BM25_INDEX_PATH", "./data/bm25_index.json")

# --- Vector store ---
QDRANT_COLLECTION = os.getenv("QDRANT_COLLECTION", "insightai_docs")
QDRANT_LOCAL_PATH = os.getenv("QDRANT_LOCAL_PATH", "./data/qdrant_local")
QDRANT_URL = os.getenv("QDRANT_URL", "")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY", "")
UPSERT_BATCH_SIZE = int(os.getenv("UPSERT_BATCH_SIZE", "100"))

# --- Retrieval ---
HYBRID_SEARCH_LIMIT = int(os.getenv("HYBRID_SEARCH_LIMIT", "10"))
RERANK_TOP_N = int(os.getenv("RERANK_TOP_N", "5"))
CROSS_ENCODER_MODEL = os.getenv("CROSS_ENCODER_MODEL", "Xenova/ms-marco-MiniLM-L-6-v2")