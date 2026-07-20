"""
InsightAI - Schema Linker for the SQL Agent.

Given a natural-language question, retrieves the subset of tables most
relevant to answering it, so the NL->SQL prompt only sees relevant schema
instead of the full database (keeps token cost down, reduces hallucinated
column references, and scales to much larger schemas later).

Follows the same "real embeddings with graceful fallback" pattern used in
Week 1's document retrieval, sized appropriately for a small (~12 table) corpus:
in-memory cosine similarity instead of a Qdrant collection.
"""
import re


import numpy as np


from db.schema_metadata import (
    ALL_TABLES,
    SCHEMA_METADATA,
    SCHEMA_ALIASES,
    table_to_document,
    format_table_for_prompt,
)

# --- Embedding backend: fastembed if available, TF-IDF/SVD fallback otherwise ---
_EMBEDDER = None
_EMBEDDER_TYPE = None


def _load_embedder():
    global _EMBEDDER, _EMBEDDER_TYPE
    if _EMBEDDER is not None:
        return
    try:
        from fastembed import TextEmbedding
        _EMBEDDER = TextEmbedding(model_name="BAAI/bge-small-en-v1.5")
        _EMBEDDER_TYPE = "fastembed"
        print("[schema_linker] Using fastembed dense embeddings")
    except Exception as e:
        print(f"[schema_linker] fastembed unavailable ({e}), falling back to TF-IDF/SVD")
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.decomposition import TruncatedSVD
        _EMBEDDER = {
            "vectorizer": TfidfVectorizer(stop_words="english"),
            "svd": TruncatedSVD(n_components=min(50, len(ALL_TABLES) - 1)),
        }
        _EMBEDDER_TYPE = "tfidf_svd"


def _embed(texts: list[str]) -> np.ndarray:
    """Embed a list of texts, returning an (n, dim) array. Fits fallback vectorizer on first call."""
    _load_embedder()
    if _EMBEDDER_TYPE == "fastembed":
        return np.array(list(_EMBEDDER.embed(texts)))
    else:
        # TF-IDF/SVD fallback - fit on first call (the schema corpus), transform thereafter
        vec = _EMBEDDER["vectorizer"]
        svd = _EMBEDDER["svd"]
        if not hasattr(vec, "vocabulary_"):
            tfidf = vec.fit_transform(texts)
            return svd.fit_transform(tfidf)
        else:
            tfidf = vec.transform(texts)
            return svd.transform(tfidf)


def _cosine_sim(query_vec: np.ndarray, doc_vecs: np.ndarray) -> np.ndarray:
    query_norm = query_vec / (np.linalg.norm(query_vec) + 1e-8)
    doc_norms = doc_vecs / (np.linalg.norm(doc_vecs, axis=1, keepdims=True) + 1e-8)
    return doc_norms @ query_norm


def _stem(token: str) -> str:
    """Very lightweight suffix-stripping stemmer - enough to bridge common
    NL question phrasing (verbs/plurals) to PascalCase schema nouns."""
    for suffix, replacement in [("ies", "y"), ("ing", ""), ("es", ""), ("s", "")]:
        if token.endswith(suffix) and len(token) > len(suffix) + 2:
            return token[: -len(suffix)] + replacement
    return token


def _keyword_overlap_score(query: str, table_name: str) -> float:
    query_lower = query.lower()
    tokens = {_stem(t) for t in re.findall(r"[a-z]+", query_lower)}
    score = 0.0

    table_tokens = {_stem(t.lower()) for t in re.findall(r"[A-Z][a-z]*", table_name)}
    if table_tokens & tokens:
        score += 0.5

    meta = SCHEMA_METADATA[table_name]
    for col in meta["columns"]:
        col_tokens = {_stem(t.lower()) for t in re.findall(r"[A-Z][a-z]*", col)}
        if col_tokens & tokens:
            score += 0.1

    
    for alias in SCHEMA_ALIASES.get(table_name, []):
        alias_tokens = {_stem(t) for t in re.findall(r"[a-z]+", alias.lower())}
        if alias_tokens & tokens:
            score += 0.4

    return min(score, 1.0)

class SchemaLinker:
    """
    Builds an in-memory searchable index over table metadata and retrieves
    the most relevant tables for a given natural-language question.
    """

    def __init__(self):
        self._table_names: list[str] = []
        self._doc_vecs: np.ndarray | None = None
        self._built = False

    def build_index(self):
        self._table_names = ALL_TABLES
        documents = [table_to_document(t) for t in self._table_names]
        self._doc_vecs = _embed(documents)
        self._built = True
        print(f"[schema_linker] Indexed {len(self._table_names)} tables")

    def retrieve(self, question: str, top_k: int = 4, semantic_weight: float = 0.75) -> list[str]:
        if not self._built:
            self.build_index()

        query_vec = _embed([question])[0]
        semantic_scores = _cosine_sim(query_vec, self._doc_vecs)
        keyword_scores = np.array(
            [_keyword_overlap_score(question, t) for t in self._table_names]
        )
        combined = semantic_weight * semantic_scores + (1 - semantic_weight) * keyword_scores

        top_indices = np.argsort(-combined)[:top_k]
        selected_indices = set(top_indices.tolist())

        # Expand with direct FK neighbors of the top-ranked table
        top_table = self._table_names[top_indices[0]]
        for fk_target in SCHEMA_METADATA[top_table]["foreign_keys"].values():
            ref_table = fk_target.split(".")[0]
            if ref_table in self._table_names:
                selected_indices.add(self._table_names.index(ref_table))

        
        ordered_indices = sorted(selected_indices, key=lambda i: -combined[i])
        return [self._table_names[i] for i in ordered_indices]

    def retrieve_with_scores(self, question: str, top_k: int = 6) -> list[tuple[str, float, float, float]]:
        """Debug helper: returns (table, semantic_score, keyword_score, combined_score) sorted by combined."""
        if not self._built:
            self.build_index()
        query_vec = _embed([question])[0]
        semantic_scores = _cosine_sim(query_vec, self._doc_vecs)
        keyword_scores = np.array(
            [_keyword_overlap_score(question, t) for t in self._table_names]
        )
        combined = 0.75 * semantic_scores + 0.25 * keyword_scores
        rows = list(zip(self._table_names, semantic_scores, keyword_scores, combined))
        rows.sort(key=lambda r: -r[3])
        return rows[:top_k]
    
    def retrieve_formatted(self, question: str, top_k: int = 4) -> str:
        """Retrieve relevant tables and format them as a prompt-ready schema string."""
        
        tables = self.retrieve(question, top_k=top_k)
        return "\n".join(format_table_for_prompt(t) for t in tables)

    



if __name__ == "__main__":
    linker = SchemaLinker()
    linker.build_index()

    test_questions = [
        "What was total revenue last quarter?",
        "Which employee has the most orders?",
        "List all products that are discontinued",
        "How many customers are in Germany?",
        "What shipping companies do we use?",
    ]

    for q in test_questions:
        print(f"\nQ: {q}")
        for table, sem, kw, comb in linker.retrieve_with_scores(q):
            print(f"  {table:22s} semantic={sem:.3f}  keyword={kw:.3f}  combined={comb:.3f}")
        print(f"  -> Final selection: {linker.retrieve(q)}")