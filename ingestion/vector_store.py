"""
Vector store module for InsightAI.

Architecture: a VectorStore class managing its client as a process-wide
SINGLETON, rather than loose functions that each expect a caller-supplied
client. This closes a real bug we hit earlier: Qdrant's local embedded
mode file-locks its storage path, so opening a second client on the same
path while one is already open raises "Storage folder is already accessed
by another instance." VectorStore.get_instance() always returns the same
client within a process, structurally, not by convention.
"""

import uuid
from typing import List, Optional

from qdrant_client import QdrantClient
from qdrant_client.http import models as qmodels

from ingestion.chunker import Chunk
from ingestion.sparse import SparseVector
from ingestion.config import (
    QDRANT_COLLECTION, QDRANT_LOCAL_PATH, QDRANT_URL, QDRANT_API_KEY,
    EMBEDDING_DIM, UPSERT_BATCH_SIZE,
)


def _batched(items: List, batch_size: int):
    for i in range(0, len(items), batch_size):
        yield items[i:i + batch_size]


class VectorStore:
    _instance: Optional["VectorStore"] = None

    def __init__(self, collection_name: str = QDRANT_COLLECTION, dim: int = EMBEDDING_DIM):
        self.collection_name = collection_name
        self.dim = dim
        self.client = self._make_client()
        self._collection_ensured = False

    @staticmethod
    def _make_client() -> QdrantClient:
        if QDRANT_URL:
            return QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY or None)
        return QdrantClient(path=QDRANT_LOCAL_PATH)

    @classmethod
    def get_instance(cls) -> "VectorStore":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def ensure_collection(self) -> None:
        if self._collection_ensured:
            return
        existing = [c.name for c in self.client.get_collections().collections]
        if self.collection_name not in existing:
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config={"dense": qmodels.VectorParams(size=self.dim, distance=qmodels.Distance.COSINE)},
                sparse_vectors_config={"sparse": qmodels.SparseVectorParams()},
            )
        self._collection_ensured = True

    def upsert_chunks(self, chunks, dense_vectors, sparse_vectors, batch_size: int = UPSERT_BATCH_SIZE) -> None:
        assert len(chunks) == len(dense_vectors) == len(sparse_vectors)
        self.ensure_collection()

        indices = list(range(len(chunks)))
        for batch_idx in _batched(indices, batch_size):
            points = []
            for i in batch_idx:
                chunk, dense_vec, sparse_vec = chunks[i], dense_vectors[i], sparse_vectors[i]
                points.append(qmodels.PointStruct(
                    id=str(uuid.uuid5(uuid.NAMESPACE_DNS, chunk.chunk_id)),
                    vector={
                        "dense": dense_vec,
                        "sparse": qmodels.SparseVector(indices=sparse_vec.indices, values=sparse_vec.values),
                    },
                    payload={
                        "chunk_id": chunk.chunk_id, "doc_name": chunk.doc_name,
                        "page_number": chunk.page_number, "text": chunk.text,
                        "token_count": chunk.token_count,
                    },
                ))
            self.client.upsert(collection_name=self.collection_name, points=points)

    def count_points(self) -> int:
        return self.client.count(collection_name=self.collection_name).count

    def hybrid_search(self, dense_query, sparse_query, limit: int = 5, prefetch_limit: int = 20):
        self.ensure_collection()
        results = self.client.query_points(
            collection_name=self.collection_name,
            prefetch=[
                qmodels.Prefetch(query=dense_query, using="dense", limit=prefetch_limit),
                qmodels.Prefetch(
                    query=qmodels.SparseVector(indices=sparse_query.indices, values=sparse_query.values),
                    using="sparse", limit=prefetch_limit,
                ),
            ],
            query=qmodels.FusionQuery(fusion=qmodels.Fusion.RRF),
            limit=limit,
        )
        return results.points

    def close(self) -> None:
        self.client.close()
        if VectorStore._instance is self:
            VectorStore._instance = None


# Module-level convenience wrappers — kept for backward compatibility with
# existing call sites, all routed through the same singleton instance.
def get_client() -> QdrantClient:
    return VectorStore.get_instance().client

def ensure_collection(client=None, dim: int = EMBEDDING_DIM) -> None:
    VectorStore.get_instance().ensure_collection()

def upsert_chunks(client, chunks, dense_vectors, sparse_vectors) -> None:
    VectorStore.get_instance().upsert_chunks(chunks, dense_vectors, sparse_vectors)

def count_points(client=None) -> int:
    return VectorStore.get_instance().count_points()

def hybrid_search(client, dense_query, sparse_query, limit: int = 5, prefetch_limit: int = 20):
    return VectorStore.get_instance().hybrid_search(dense_query, sparse_query, limit, prefetch_limit)