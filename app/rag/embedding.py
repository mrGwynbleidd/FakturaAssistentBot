# from pathlib import Path

# MODEL_PATH = Path(__file__).resolve().parents[2] / "models" / "embedding_model"

# if MODEL_PATH.exists():
#     embedding_model = SentenceTransformer(str(MODEL_PATH))
# else:
#     embedding_model = SentenceTransformer("sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")


#import sentence transformar
from sentence_transformers import SentenceTransformer

#model of transformer
MODEL_NAME = "paraphrase-multilingual-MiniLM-L12-v2"

#create model
embedding_model = SentenceTransformer(MODEL_NAME)

#embedding text locally. used in retrivier for question
def get_embedding(text: str) -> list[float]:

    embedding = embedding_model.encode(text)

    return embedding.tolist()

#create embedding for list of text. used in index_builder
def get_embeddings(texts: list[str]) -> list[list[float]]:

    import logging
    logging.getLogger("bot").info(f"Embedding {len(texts)} fragments...")

    embedding = embedding_model.encode(
        texts,
        show_progress_bar=True,
        batch_size=32,

    )

    return embedding.tolist()