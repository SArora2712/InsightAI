"""
Chunking module for InsightAI.

Splits parsed documents into overlapping chunks sized for embedding, while
preserving source metadata (doc name, page number, chunk index) needed for
citation later in the RAG pipeline.

"""

from dataclasses import dataclass
from typing import List

from ingestion.parser import ParsedDocument, PageContent
from ingestion.tokenizer import bpe_token_len, bpe_encode, bpe_decode
from ingestion.config import CHUNK_SIZE, CHUNK_OVERLAP

DEFAULT_CHUNK_SIZE = CHUNK_SIZE
DEFAULT_CHUNK_OVERLAP = CHUNK_OVERLAP


@dataclass
class Chunk:
    chunk_id: str
    doc_name: str
    page_number: int
    text: str
    token_count: int


def _split_page_into_chunks(
    page: PageContent,
    chunk_size: int,
    chunk_overlap: int,
) -> List[str]:
    """Split a single page's text into a token-level sliding window, with
    every chunk overlapping the previous one by `chunk_overlap` tokens —
    not just when a single paragraph happens to be oversized."""
    paragraphs = [p.strip() for p in page.text.split("\n") if p.strip()]
    if not paragraphs:
        return []

    full_text = " ".join(paragraphs)
    tokens = bpe_encode(full_text)
    if not tokens:
        return []

    step = max(1, chunk_size - chunk_overlap)
    chunks = []
    i = 0
    while i < len(tokens):
        window = tokens[i:i + chunk_size]
        if not window:
            break
        chunks.append(bpe_decode(window))
        if i + chunk_size >= len(tokens):
            break
        i += step

    return chunks


def chunk_document(
    doc: ParsedDocument,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    chunk_overlap: int = DEFAULT_CHUNK_OVERLAP,
) -> List[Chunk]:
    """Chunk an entire parsed document, page by page, preserving citations."""
    all_chunks: List[Chunk] = []
    running_idx = 0

    for page in doc.pages:
        page_chunks = _split_page_into_chunks(page, chunk_size, chunk_overlap)
        for text in page_chunks:
            all_chunks.append(
                Chunk(
                    chunk_id=f"{doc.doc_name}_p{page.page_number}_c{running_idx}",
                    doc_name=doc.doc_name,
                    page_number=page.page_number,
                    text=text,
                    token_count=bpe_token_len(text),
                )
            )
            running_idx += 1

    return all_chunks


if __name__ == "__main__":
    from ingestion.parser import parse_directory

    docs = parse_directory("data/raw")
    for d in docs:
        chunks = chunk_document(d, chunk_size=120, chunk_overlap=20)
        print(f"\n=== {d.doc_name}: {len(chunks)} chunks ===")
        for i, c in enumerate(chunks):
            print(f"  [{c.chunk_id}] ({c.token_count} tok) {c.text[:90]}...")