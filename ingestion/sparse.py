"""
Sparse vector module for InsightAI — classic BM25, implemented directly.

Unlike dense embeddings, BM25 doesn't need a neural model — it's a
statistical formula over term frequencies in your own corpus, computed
once at fit time. That fitted state (vocabulary, document frequencies,
average document length) is now persisted to disk instead of being
rebuilt from scratch on every run.

BM25(t, d) = idf(t) * ( tf(t,d) * (k1+1) ) / ( tf(t,d) + k1 * (1 - b + b * |d|/avgdl) )

Tokenization now lives in tokenizer.py, shared with anything else that
needs word-level (vs. BPE) tokens.
"""

import json
import math
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import List, Dict

from ingestion.tokenizer import word_tokenize
from ingestion.config import BM25_K1, BM25_B, BM25_INDEX_PATH


@dataclass
class SparseVector:
    indices: List[int]
    values: List[float]


class BM25Index:
    """Fit once on a corpus, then produce a BM25 sparse vector for any text.
    Can be saved to / loaded from disk so fitting doesn't have to happen
    on every process start."""

    def __init__(self, k1: float = BM25_K1, b: float = BM25_B):
        self.k1 = k1
        self.b = b
        self.vocab: Dict[str, int] = {}
        self.doc_freq: Counter = Counter()
        self.avgdl: float = 0.0
        self.n_docs: int = 0
        self._fitted = False

    def fit(self, corpus: List[str]) -> None:
        doc_token_lists = [word_tokenize(text) for text in corpus]
        self.n_docs = len(doc_token_lists)
        self.avgdl = sum(len(toks) for toks in doc_token_lists) / max(1, self.n_docs)

        self.vocab = {}
        self.doc_freq = Counter()
        for toks in doc_token_lists:
            for term in set(toks):
                if term not in self.vocab:
                    self.vocab[term] = len(self.vocab)
                self.doc_freq[term] += 1

        self._fitted = True

    def _idf(self, term: str) -> float:
        df = self.doc_freq.get(term, 0)
        return max(0.01, math.log((self.n_docs - df + 0.5) / (df + 0.5) + 1))

    def encode(self, text: str) -> SparseVector:
        if not self._fitted:
            raise RuntimeError("BM25Index.fit(corpus) or .load() must be called before encode().")

        tokens = word_tokenize(text)
        doc_len = len(tokens)
        tf = Counter(tokens)

        indices, values = [], []
        for term, freq in tf.items():
            if term not in self.vocab:
                continue
            idf = self._idf(term)
            denom = freq + self.k1 * (1 - self.b + self.b * doc_len / max(1.0, self.avgdl))
            score = idf * (freq * (self.k1 + 1)) / denom
            indices.append(self.vocab[term])
            values.append(float(score))

        return SparseVector(indices=indices, values=values)

    def save(self, path: str = BM25_INDEX_PATH) -> None:
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        state = {
            "k1": self.k1, "b": self.b, "vocab": self.vocab,
            "doc_freq": dict(self.doc_freq), "avgdl": self.avgdl, "n_docs": self.n_docs,
        }
        with open(path, "w") as f:
            json.dump(state, f)

    @classmethod
    def load(cls, path: str = BM25_INDEX_PATH) -> "BM25Index":
        with open(path, "r") as f:
            state = json.load(f)
        idx = cls(k1=state["k1"], b=state["b"])
        idx.vocab = state["vocab"]
        idx.doc_freq = Counter(state["doc_freq"])
        idx.avgdl = state["avgdl"]
        idx.n_docs = state["n_docs"]
        idx._fitted = True
        return idx

    @classmethod
    def exists(cls, path: str = BM25_INDEX_PATH) -> bool:
        return Path(path).exists()


def fit_or_load(corpus: List[str], path: str = BM25_INDEX_PATH, force_refit: bool = False) -> BM25Index:
    """Load a persisted index if one exists, otherwise fit fresh and save.
    Set force_refit=True after adding new documents to the corpus."""
    if not force_refit and BM25Index.exists(path):
        print(f"[sparse] Loaded persisted BM25 index from {path}.")
        return BM25Index.load(path)

    print(f"[sparse] Fitting BM25 index on {len(corpus)} documents...")
    idx = BM25Index()
    idx.fit(corpus)
    idx.save(path)
    print(f"[sparse] Saved BM25 index to {path}.")
    return idx