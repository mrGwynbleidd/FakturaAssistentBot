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

    print(f"Creating local embedding for {len(texts)} fragments...")

    embedding = embedding_model.encode(
        texts,
        show_progress_bar=True,
        batch_size=32,

    )

    return embedding.tolist()