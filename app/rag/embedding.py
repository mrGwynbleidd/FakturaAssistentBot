# # from pathlib import Path

# # MODEL_PATH = Path(__file__).resolve().parents[2] / "models" / "embedding_model"

# # if MODEL_PATH.exists():
# #     embedding_model = SentenceTransformer(str(MODEL_PATH))
# # else:
# #     embedding_model = SentenceTransformer("sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")


# #import sentence transformar
# from sentence_transformers import SentenceTransformer

# #model of transformer
# MODEL_NAME = "paraphrase-multilingual-MiniLM-L12-v2"

# #create model
# embedding_model = SentenceTransformer(MODEL_NAME)

# #embedding text locally. used in retrivier for question
# def get_embedding(text: str) -> list[float]:

#     embedding = embedding_model.encode(text)

#     return embedding.tolist()

# #create embedding for list of text. used in index_builder
# def get_embeddings(texts: list[str]) -> list[list[float]]:

#     import logging
#     logging.getLogger("bot").info(f"Embedding {len(texts)} fragments...")

#     embedding = embedding_model.encode(
#         texts,
#         show_progress_bar=True,
#         batch_size=32,

#     )

#     return embedding.tolist()


#loads and caches the sentence transformer embedding model, embeds text into vectors
#used by index_builder and priority_retriever for all chroma queries and indexing

from functools import lru_cache
from app.rag.settings import EMBEDDING_MODEL_NAME

#lazily loads the model on first call and caches it for the process lifetime
#returns SentenceTransformer instance
def get_embedding_model():
    try:
        from sentence_transformers import SentenceTransformer
    except ImportError as err:
        raise RuntimeError(
            "sentence-transformers не установлен. Выполните pip install sentence-transformers"
        ) from err
    return SentenceTransformer(EMBEDDING_MODEL_NAME)

#caches the model instance so it is only loaded once
get_embedding_model = lru_cache(maxsize=1)(get_embedding_model)

#embeds a list of texts into normalized float vectors, returns empty list if input is empty
#used in index_builder.add_documents_to_collection and approved_index_updater
def embed_texts(texts: list[str]) -> list[list[float]]:
    if not texts:
        return []
    
    model = get_embedding_model()
    embeddings = model.encode(texts, normalize_embeddings=True, show_progress_bar=False)
    return embeddings.tolist()

#embeds a single text string, returns a single float vector
#used in priority_retriever.search_collection
def embed_text(text: str) -> list[float]:
    return embed_texts([text])[0]
