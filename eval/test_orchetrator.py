from ingestion.parser import parse_directory
from ingestion.chunker import chunk_document
from ingestion.vector_store import get_client, ensure_collection, upsert_chunks
from ingestion.sparse import BM25Index
from ingestion.embeddings import get_provider
from agents.orchestrator.graph import build_orchestrator_graph  # adjust path if orchestrator lives elsewhere

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

test_questions = [
    "What was total revenue by category last quarter?",
    "Who is the current Federal Reserve chair?",
    "What is driving customer churn?",
]

for q in test_questions:
    print(f"\n{'='*60}\nQ: {q}")
    result = app.invoke({"query": q, "agents_needed": [], "rag_result": None, "sql_result": None, "web_result": None})
    print(f"Agents used: {result['agents_needed']}")
   
    print(f"\nFinal answer:\n{result['final_answer']}")
client.close()