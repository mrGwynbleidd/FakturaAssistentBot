#read approved cases

#import libs
import csv
from pathlib import Path

#base dir
BASE_DIR = Path(__file__).resolve().parents[2]

#path where to load data
APPROVED_CASES_PATH = BASE_DIR / "data" / "learning" / "approved.csv"

#load approved cases and convert it in docs for Chroma
def load_approved_cases() -> list[dict]:
    
    #if file is empty
    if not APPROVED_CASES_PATH.exists():
        return []
    
    #arr will consist text from approved cases
    documents = []


    #read data from csv
    with open(APPROVED_CASES_PATH, mode="r", encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)

        
        for row in reader:
            status = row.get("status", "approved").strip().lower()

            if status and status != "approved":
                continue

            question = row.get("question", "").strip()
            answer = row.get("approved_answer", "").strip()
            language = row.get("language", "unknown").strip()
            category = row.get("category", "general").strip()
            case_id = row.get("case_id", "").strip()
            source_type = row.get("source_type", "admin_review").strip()
            source_id = row.get("source_id", "").strip()

            #if question or answer is empty
            if not question or not answer:
                continue
            #output text
            text = f"""
User question: {question}

Correct answer: {answer}
""".strip()
            
            
            #add data in docs
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

    #return
    return documents


