from ingestion.vector_store import VectorStore

vs = VectorStore.get_instance()
print(f"Deleting collection: {vs.collection_name}")
vs.client.delete_collection(vs.collection_name)
vs.close()
print("Done — collection cleared.")