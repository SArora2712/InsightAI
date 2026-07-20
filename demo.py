"""
InsightAI - Live demo script (Workflow mode, demo-hardened question set).
Agent mode exists and works but is shown separately/verbally as the
architecture evolution story - not driven live with unscripted questions yet.
"""
from ingestion.parser import parse_directory
from ingestion.chunker import chunk_document
from ingestion.vector_store import get_client, ensure_collection, upsert_chunks
from ingestion.sparse import BM25Index
from ingestion.embeddings import get_provider
from agents.orchestrator.graph import build_orchestrator_graph

print("=" * 70)
print("INSIGHTAI — Multi-Agent Business Analyst Copilot")
print("=" * 70)
print("\n[Setup] Ingesting documents and building indices...\n")

docs = parse_directory("data/raw")
all_chunks = []
for d in docs:
    all_chunks.extend(chunk_document(d, chunk_size=120, chunk_overlap=20))
texts = [c.text for c in all_chunks]

provider = get_provider()
provider.fit_if_needed(texts)
dense_vectors = provider.embed_texts(texts)

bm25 = BM25Index()
bm25.fit(texts)
sparse_vectors = [bm25.encode(t) for t in texts]

client = get_client()
ensure_collection(client)
upsert_chunks(client, all_chunks, dense_vectors, sparse_vectors)

app = build_orchestrator_graph(bm25, provider, client)
print(f"[Setup] Indexed {len(all_chunks)} chunks. Ready.\n")

# Confirmed clean across testing - safe to demo live
demo_questions = [
    ("SQL Agent — real company data",
     "What was total revenue by category?"),
    ("Web Search Agent — live internet, not stale training data",
     "Who is the current Federal Reserve chair?"),
    ("Document RAG — internal report retrieval",
     "What was total Beverages category revenue, and does that match what the internal report says?"),
    ("Out-of-scope handling — honest refusal, not fabrication",
     "What is programming?"),
     ("Out-of-scope handling — honest refusal, not fabrication",
    "tell me a joke"),
     ("Out-of-scope handling — honest refusal, not fabrication",
     "how to train a ml model?"),
     ("Out-of-scope handling — honest refusal, not fabrication",
     "Write apoem on nature?"),
     ("Out-of-scope handling — honest refusal, not fabrication",
     "solve the mathematics question :A store is offering a 20% discount on all items. If an additional 5% off is applied at the register, what is the final cost of an item originally priced at ₹250?")
]

for label, question in demo_questions:
    print("\n" + "=" * 70)
    print(f"DEMO: {label}")
    print("=" * 70)
    print(f"Q: {question}\n")
    result = app.invoke({
        "query": question, "agents_needed": [],
        "rag_result": None, "sql_result": None, "web_result": None,
        "final_answer": None, "conflict_detected": None, "conflict_summary": None,
        "confidence": None, "critique": None,
    })
    print(f"Agents routed to: {result['agents_needed']}")
    if result.get("conflict_detected"):
        print(f"⚠️ CONFLICT: {result['conflict_summary']}")
    conf = result.get("confidence") or {}
    print(f"Confidence: {conf.get('label')} ({conf.get('score')})")
    print(f"\nAnswer:\n{result['final_answer']}\n")

client.close()
print("=" * 70)
print("Demo complete.")