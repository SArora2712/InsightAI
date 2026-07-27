"""
Standalone test for agents/agentic/graph_loop.py — run before wiring the
LangGraph version into the actual app. Compares behavior against what
loop.py already produces for the same questions.
"""
from ingestion.embeddings import get_provider
from ingestion.sparse import BM25Index
from ingestion.parser import parse_directory
from ingestion.chunker import chunk_document
from ingestion.vector_store import get_client, ensure_collection

from agents.agentic.agent import build_agent_tools
from agents.agentic.graph_loop import run_agentic_query_v2


def _build_bm25_and_provider():
    docs = parse_directory("data/raw")
    all_chunks = []
    for d in docs:
        all_chunks.extend(chunk_document(d, chunk_size=120, chunk_overlap=20))
    texts = [c.text for c in all_chunks]

    provider = get_provider()
    provider.fit_if_needed(texts)

    bm25 = BM25Index()
    bm25.fit(texts)
    return bm25, provider


def run_test(label: str, question: str, tool_dispatch: dict,max_iterations:int = 5):
    print(f"\n{'=' * 70}")
    print(f"TEST: {label}")
    print(f"Question: {question}")
    print('=' * 70)

    result = run_agentic_query_v2(question, tool_dispatch,max_iteration=max_iterations)


    print(f"\nIterations: {result['iterations']}")
    print(f"Tool calls made: {len(result['tool_calls_made'])}")
    for tc in result["tool_calls_made"]:
        print(f"  - {tc['tool']}({tc['args']})")
    print(f"\nAnswer:\n{result['answer']}")
    print()


if __name__ == "__main__":
    print("Setting up tools (this loads the vector store + BM25 index)...")
    bm25, provider = _build_bm25_and_provider()
    client = get_client()
    ensure_collection(client)

    tool_dispatch = build_agent_tools(bm25, provider, client)

    # Test 1: should resolve cleanly through the `finalize` path
    run_test(
        "Clean single-tool resolution",
        "What was total revenue by category?",
        tool_dispatch,
    )

    # Test 2: out-of-scope pre-check — should never touch the graph at all
    run_test(
        "Out-of-scope pre-check",
        "What is photosynthesis?",
        tool_dispatch,
    )

    # Test 3: should require multiple tool calls, exercising the tools -> agent loop-back
    run_test(
        "Multi-tool loop-back",
        "How did our sales perform, and how might current inflation affect future sales, based on our internal reports?",
        tool_dispatch,
    )

    # Test 4: force the capped-iteration fallback path
    run_test(
        "Forced iteration cap (fallback path)",
        "How did our sales perform, and how might current inflation affect future sales, based on our internal reports?",
        tool_dispatch,
        max_iterations=1,
    )

    print(f"\n{'=' * 70}")
    print("All tests complete. Compare answers/behavior against loop.py's")
    print("run_agentic_query for the same questions if you want a direct diff.")
    print('=' * 70)

    client.close()