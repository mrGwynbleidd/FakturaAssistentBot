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



from functools import lru_cache
from app.rag.settings import EMBEDDING_MODEL_NAME

@lru_cache(maxsize=1)
def get_embedding_model():
    try:
        from sentence_transformers import SentenceTransformer
    except ImportError as err:
        raise RuntimeError(
            "sentence-transformers не установлен. Выполните pip install sentence-transformers"
        ) from err
    return SentenceTransformer(EMBEDDING_MODEL_NAME)

def embed_texts(texts: list[str]) -> list[list[float]]:
    if not texts:
        return []
    
    model = get_embedding_model()
    embeddings = model.encode(texts, normalize_embeddings=True, show_progress_bar=False)
    return embeddings.tolist()

def embed_text(text: str) -> list[float]:
    return embed_texts([text])[0]