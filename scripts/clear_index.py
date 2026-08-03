import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from ingestion.vector_store import VectorStore

vs = VectorStore.get_instance()
print(f"Deleting collection: {vs.collection_name}")
vs.client.delete_collection(vs.collection_name)
vs.close()
print("Done — collection cleared.")