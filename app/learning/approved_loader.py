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
            question = row.get("question", "").strip()
            answer = row.get("approved_answer", "").strip()
            language = row.get("language", "unknown")
            category = row.get("category", "general")
            case_id = row.get("case_id", "")

            #if question or answer is empty
            if not question or not answer:
                continue
            #output text
            text = f"""
User question: {question}

Correct answer: {answer}
"""
            #add data in docs
            documents.append(
                {
                    "source": f"approved_case:{case_id}",
                    "text": text.strip(),
                    "metadata": {
                        "source": f"approved case: {case_id}",
                        "language": language,
                        "category": category,
                        "source_type": "admin_review",
                    },
                }
            )

            #return
            return documents


