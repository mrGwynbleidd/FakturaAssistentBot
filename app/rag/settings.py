
from pathlib import Path
import os

BASE_DIR = Path(__file__).resolve().parents[2]

DATA_DIR = BASE_DIR / "data"
CHROMA_DIR = DATA_DIR / "chroma_db"
PDF_DIR = DATA_DIR / "pdf"
APPROVED_CSV_PATH = DATA_DIR / "learning" / "approved.csv"
ADMIN_KNOWLEDGE_CSV_PATH = DATA_DIR / "admin" / "admin_knowledge.csv"


COLLECTION_APPROVED = "faktura_approved_cases"
COLLECTION_ADMIN_KNOWLEDGE = "faktura_admin_knowledge"
COLLECTION_PDF = "faktura_pdf_knowledge"

EMBEDDING_MODEL_NAME = os.getenv(
    "EMBEDDING_MODEL",
    "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
)

APPROVED_DIRECT_THRESHOLD = float(os.getenv("APPROVED_DIRECT_THRESHOLD", "0.78"))
ADMIN_DIRECT_THRESHOLD = float(os.getenv("ADMIN_DIRECT_THRESHOLD", "0.82"))
APPROVED_CONTEXT_THRESHOLD = float(os.getenv("APPROVED_CONTEXT_THRESHOLD", "0.55"))
ADMIN_CONTEXT_THRESHOLD = float(os.getenv("ADMIN_CONTEXT_THRESHOLD", "0.55"))
PDF_CONTEXT_THRESHOLD = float(os.getenv("PDF_CONTEXT_THRESHOLD", "0.35"))
MAX_APPROVED_RESULTS = int(os.getenv("MAX_APPROVED_RESULTS", "5"))
MAX_ADMIN_RESULTS = int(os.getenv("MAX_ADMIN_RESULTS", "5"))
MAX_PDF_RESULTS = int(os.getenv("MAX_PDF_RESULTS", "7"))
PDF_CHUNK_SIZE = int(os.getenv("PDF_CHUNK_SIZE", "1200"))
PDF_CHUNK_OVERLAP = int(os.getenv("PDF_CHUNK_OVERLAP", "180"))
