"""
Compare the original Python agentic loop against the LangGraph implementation.
"""

from ingestion.embeddings import get_provider
from ingestion.sparse import BM25Index
from ingestion.parser import parse_directory
from ingestion.chunker import chunk_document
from ingestion.vector_store import get_client, ensure_collection

from agents.agentic.agent import build_agent_tools
from agents.agentic.agent import run_agentic_query
from agents.agentic.graph_loop import run_agentic_query_v2


def _build_bm25_and_provider():
    docs = parse_directory("data/raw")

    all_chunks = []

    for d in docs:
        all_chunks.extend(
            chunk_document(
                d,
                chunk_size=120,
                chunk_overlap=20
            )
        )

    texts = [c.text for c in all_chunks]

    provider = get_provider()
    provider.fit_if_needed(texts)

    bm25 = BM25Index()
    bm25.fit(texts)

    return bm25, provider


def compare_results(question, old_result, new_result):

    print("\n" + "=" * 70)
    print(f"QUESTION: {question}")
    print("=" * 70)

    print("\n--- OLD LOOP ---")
    print(f"Iterations: {old_result['iterations']}")
    print(
        f"Tool calls: "
        f"{len(old_result['tool_calls_made'])}"
    )

    for tc in old_result["tool_calls_made"]:
        print(
            f"  - {tc['tool']}"
            f"({tc['args']})"
        )

    print("\nAnswer:")
    print(old_result["answer"])

    print("\n--- LANGGRAPH LOOP ---")
    print(f"Iterations: {new_result['iterations']}")
    print(
        f"Tool calls: "
        f"{len(new_result['tool_calls_made'])}"
    )

    for tc in new_result["tool_calls_made"]:
        print(
            f"  - {tc['tool']}"
            f"({tc['args']})"
        )

    print("\nAnswer:")
    print(new_result["answer"])

    print("\n--- COMPARISON ---")

    old_tools = [
        tc["tool"]
        for tc in old_result["tool_calls_made"]
    ]

    new_tools = [
        tc["tool"]
        for tc in new_result["tool_calls_made"]
    ]

    if old_tools == new_tools:
        print("✓ Tool sequence matches")
    else:
        print("⚠ Tool sequence differs")

    if old_result["iterations"] == new_result["iterations"]:
        print("✓ Iteration count matches")
    else:
        print(
            "⚠ Iteration count differs: "
            f"old={old_result['iterations']}, "
            f"new={new_result['iterations']}"
        )


if __name__ == "__main__":

    print(
        "Setting up tools "
        "(this loads the vector store + BM25 index)..."
    )

    bm25, provider = _build_bm25_and_provider()

    client = get_client()
    ensure_collection(client)

    tool_dispatch = build_agent_tools(
        bm25,
        provider,
        client
    )

    questions = [
        "What was total revenue by category?",

        "What is photosynthesis?",

        "How did our sales perform, and how might current inflation affect "
        "future sales, based on our internal reports?",
    ]

    for question in questions:

        print("\n\nRunning OLD loop...")

        old_result = run_agentic_query(
            question,
            tool_dispatch
        )

        print("\nRunning NEW LangGraph loop...")

        new_result = run_agentic_query_v2(
            question,
            tool_dispatch
        )

        compare_results(
            question,
            old_result,
            new_result
        )

    client.close()