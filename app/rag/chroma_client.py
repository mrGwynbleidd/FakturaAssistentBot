#manages the persistent chromadb client and collection access
#used by index_builder, priority_retriever, and approved_index_updater

import chromadb
from app.rag.settings import CHROMA_DIR

#creates a persistent chroma client at CHROMA_DIR, creating the directory if needed
#used internally by get_or_create_collection and reset_collection
def get_chroma_client():
    CHROMA_DIR.mkdir(parents=True, exist_ok=True)
    return chromadb.PersistentClient(path=str(CHROMA_DIR))

#returns an existing collection or creates it with cosine similarity space
#used in priority_retriever and approved_index_updater
def get_or_create_collection(name: str):
    client = get_chroma_client()
    return client.get_or_create_collection(name=name,metadata={"hnsw:space": "cosine"})

#deletes a collection if it exists and recreates it with cosine similarity space
#used in index_builder when rebuilding indexes
def reset_collection(name: str):
    client = get_chroma_client()
    try:
        client.delete_collection(name=name)
    except Exception:
        pass
    return client.get_or_create_collection(name=name, metadata={"hnsw:space": "cosine"})
