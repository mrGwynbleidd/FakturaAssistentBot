#loads approved Q&A pairs from approved.csv and converts them to chroma document dicts
#legacy loader — kept for compatibility with older code paths
#used in learning pipeline scripts

#import libs
import csv
from pathlib import Path

#base dir
BASE_DIR = Path(__file__).resolve().parents[2]

#path to approved cases csv
APPROVED_CASES_PATH = BASE_DIR / "data" / "learning" / "approved.csv"

#reads approved.csv and returns list of document dicts with text and metadata
#skips rows with missing question or answer, and rows with non-approved status
#used in legacy index build scripts
def load_approved_cases() -> list[dict]:
    
    if not APPROVED_CASES_PATH.exists():
        return []
    
    #accumulates converted document dicts
    documents = []

    with open(APPROVED_CASES_PATH, mode="r", encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)

        for row in reader:
            status = row.get("status", "approved").strip().lower()

            #skip rows with any non-approved status
            if status and status != "approved":
                continue

            question = row.get("question", "").strip()
            answer = row.get("approved_answer", "").strip()
            language = row.get("language", "unknown").strip()
            category = row.get("category", "general").strip()
            case_id = row.get("case_id", "").strip()
            source_type = row.get("source_type", "admin_review").strip()
            source_id = row.get("source_id", "").strip()

            #skip incomplete rows
            if not question or not answer:
                continue

            #format text block for embedding
            text = f"""
User question: {question}

Correct answer: {answer}
""".strip()
            
            #build document dict for chroma
            documents.append(
                {
                    "source": f"{source_type}:{source_id or case_id}",
                    "text": text,
                    "metadata": {
                        "source": f"{source_type}: {source_id or case_id}",
                        "case_id": case_id,
                        "language": language,
                        "category": category,
                        "source_id": source_id,
                    },
                }
            )

    return documents
