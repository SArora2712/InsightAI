"""
Shared tokenization for InsightAI.

Two genuinely different tokenizers are used across the pipeline, and both
live here so dense chunking and sparse BM25 never silently diverge in how
they define a "token":

- BPE tokenizer (tiktoken cl100k_base) — used by the chunker, since it
  needs to size chunks the same way the LLM will actually consume them.
  Falls back to a word-count approximation if tiktoken's remote encoding
  file is unreachable (see bpe_token_len).
- Word tokenizer — used by BM25 sparse vectors, where exact terms/keywords
  matter more than subword pieces. Lowercases, strips punctuation, drops
  English stopwords and single-character tokens.
"""

import re
from typing import List

from sklearn.feature_extraction.text import ENGLISH_STOP_WORDS

try:
    import tiktoken
    _ENCODER = tiktoken.get_encoding("cl100k_base")
except Exception:
    _ENCODER = None

USING_BPE_TOKENIZER = _ENCODER is not None


def bpe_token_len(text: str) -> int:
    if _ENCODER is not None:
        return len(_ENCODER.encode(text))
    return max(1, int(len(text.split()) / 0.75))


def bpe_encode(text: str) -> List:
    if _ENCODER is not None:
        return _ENCODER.encode(text)
    return text.split()


def bpe_decode(tokens: List) -> str:
    if _ENCODER is not None:
        return _ENCODER.decode(tokens)
    return " ".join(tokens)


_WORD_RE = re.compile(r"[a-z0-9]+")


def word_tokenize(text: str) -> List[str]:
    """Word-level tokenizer for BM25: lowercase, alphanumeric only,
    stopwords removed, single-character tokens dropped."""
    tokens = _WORD_RE.findall(text.lower())
    return [t for t in tokens if t not in ENGLISH_STOP_WORDS and len(t) > 1]