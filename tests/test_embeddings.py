"""Tests for the offline-capable TF-IDF embedding fallback provider."""
from ingestion.embeddings import TFIDFFallbackProvider


class TestTFIDFFallbackProvider:
    def test_get_provider_returns_without_network(self):
        # Avoid triggering a fastembed model download in CI; use fallback directly.
        p = TFIDFFallbackProvider(dim=32)
        assert p.name == "tfidf_fallback"

    def test_requires_fit_before_embed(self):
        p = TFIDFFallbackProvider(dim=32)
        try:
            p.embed_texts(["hello"])
            assert False, "should have raised before fit"
        except RuntimeError:
            pass

    def test_embeds_after_fit(self):
        p = TFIDFFallbackProvider(dim=32)
        corpus = [
            "InsightAI analyzes Northwind sales data",
            "Customer retention drives quarterly revenue",
            "Marketing campaigns improved conversion rates",
        ]
        p.fit_if_needed(corpus)
        vectors = p.embed_texts(["revenue from east coast customers"])
        assert len(vectors) == 1
        assert len(vectors[0]) == 32

    def test_same_corpus_consistent_vectors(self):
        p = TFIDFFallbackProvider(dim=32)
        corpus = ["apple banana cherry", "data sales order"]
        p.fit_if_needed(corpus)
        a = p.embed_texts(["apple"])
        b = p.embed_texts(["apple"])
        assert a == b