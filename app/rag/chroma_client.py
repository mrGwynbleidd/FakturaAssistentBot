
import chromadb
from app.rag.settings import CHROMA_DIR

def get_chroma_client():
    CHROMA_DIR.mkdir(parents=True, exist_ok=True)
    return chromadb.PersistentClient(path=str(CHROMA_DIR))

def get_or_create_collection(name: str):
    client = get_chroma_client()
    return client.get_or_create_collection(name=name,metadata={"hnsw:space": "cosine"})

def reset_collection(name: str):
    client = get_chroma_client()
    try:
        client.delete_collection(name=name)
    except Exception:
        pass
    return client.get_or_create_collection(name=name, metadata={"hnsw:space": "cosine"})


