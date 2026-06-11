#call function from index_builder
from sentence_transformers import SentenceTransformer
model = SentenceTransformer("sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")
model.save("./models/embedding_model")

from app.rag.index_builder import build_index

build_index()