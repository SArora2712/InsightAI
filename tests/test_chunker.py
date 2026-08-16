"""Tests for document chunking."""
from ingestion.chunker import chunk_document
from ingestion.parser import PageContent, ParsedDocument


def _make_doc(pages_text):
    doc = ParsedDocument(doc_name="test", source_path="/tmp/test.pdf")
    for i, text in enumerate(pages_text, start=1):
        doc.pages.append(PageContent(doc_name="test", page_number=i, text=text))
    return doc


class TestChunkDocument:
    def test_empty_page_produces_no_chunks(self):
        chunks = chunk_document(_make_doc([""]))
        assert chunks == []

    def test_long_text_is_split(self):
        text = "product category customer order supplier revenue " * 60
        chunks = chunk_document(_make_doc([text]), chunk_size=50, chunk_overlap=10)
        assert len(chunks) >= 1
        for c in chunks:
            assert c.doc_name == "test"
            assert c.token_count > 0

    def test_chunk_metadata_preserved(self):
        chunks = chunk_document(_make_doc(["page one content " * 20]), chunk_size=50, chunk_overlap=10)
        for c in chunks:
            assert c.chunk_id.startswith("test_p1_c")
            assert c.page_number == 1

    def test_multiple_pages_keep_page_numbers(self):
        doc = _make_doc(["a b c d " * 30, "page two text " * 40])
        chunks = chunk_document(doc, chunk_size=50, chunk_overlap=10)
        pages = {c.page_number for c in chunks}
        assert pages == {1, 2}