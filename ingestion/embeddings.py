"""
Dense embedding module for InsightAI.

Architected around a provider abstraction rather than a single hardcoded
path, so swapping embedding backends later is a config change, not a rewrite:

- EmbeddingProvider: abstract interface (embed_texts, fit_if_needed)
- FastEmbedProvider: real neural embeddings (BAAI/bge-small-en-v1.5)
- TFIDFFallbackProvider: offline-capable fallback when the model download
  is blocked (restricted sandboxes, no internet yet, corporate proxies)

Both providers batch their inputs (EMBEDDING_BATCH_SIZE from config.py).
"""

from abc import ABC, abstractmethod
from typing import List

from ingestion.config import EMBEDDING_DIM, DENSE_MODEL_NAME, EMBEDDING_BATCH_SIZE


def _batched(items: List, batch_size: int):
    for i in range(0, len(items), batch_size):
        yield items[i:i + batch_size]


class EmbeddingProvider(ABC):
    name: str = "base"

    @abstractmethod
    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        ...

    def fit_if_needed(self, corpus: List[str]) -> None:
        pass


class FastEmbedProvider(EmbeddingProvider):
    name = "fastembed"

    def __init__(self, model_name: str = DENSE_MODEL_NAME, batch_size: int = EMBEDDING_BATCH_SIZE):
        from fastembed import TextEmbedding
        self._model = TextEmbedding(model_name=model_name)
        self._batch_size = batch_size

    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        out = []
        for batch in _batched(texts, self._batch_size):
            out.extend(v.tolist() for v in self._model.embed(batch))
        return out


class TFIDFFallbackProvider(EmbeddingProvider):
    name = "tfidf_fallback"

    def __init__(self, dim: int = EMBEDDING_DIM, batch_size: int = EMBEDDING_BATCH_SIZE):
        self._dim = dim
        self._batch_size = batch_size
        self._tfidf = None
        self._svd = None
        self._fitted = False

    def fit_if_needed(self, corpus: List[str]) -> None:
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.decomposition import TruncatedSVD

        self._tfidf = TfidfVectorizer(max_features=2000, stop_words="english")
        self._svd = TruncatedSVD(n_components=min(self._dim, max(2, len(corpus) - 1)))
        matrix = self._tfidf.fit_transform(corpus)
        self._svd.fit(matrix)
        self._fitted = True

    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        if not self._fitted:
            raise RuntimeError("fit_if_needed(corpus) must be called before embed_texts().")

        out = []
        for batch in _batched(texts, self._batch_size):
            matrix = self._tfidf.transform(batch)
            reduced = self._svd.transform(matrix)
            for row in reduced:
                row = list(row)
                if len(row) < self._dim:
                    row = row + [0.0] * (self._dim - len(row))
                out.append(row[:self._dim])
        return out


def get_provider() -> EmbeddingProvider:
    try:
        provider = FastEmbedProvider()
        print(f"[embeddings] Using {provider.name} ({DENSE_MODEL_NAME}) — real neural embeddings.")
        return provider
    except Exception as e:
        print(f"[embeddings] fastembed unavailable ({type(e).__name__}), falling back to TF-IDF.")
        return TFIDFFallbackProvider()