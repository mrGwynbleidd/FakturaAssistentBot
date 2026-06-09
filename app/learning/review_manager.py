#Add correct answer

#import libs
import csv
from pathlib import Path

#base path
BASE_DIR = Path(__file__).resolve().parents[2]

#path where bad answer stored for now not used
NEEDS_REVIEW_PATH = BASE_DIR / "data" / "learning" / "needs_review.csv"
#path where correct answer will be saved
APPROVED_CASES_PATH = BASE_DIR / "data" / "learning" / "approved.csv"

#fieldnames for csv
APPROVED_FIELDNAMES = [
    "case_id",
    "language",
    "question",
    "approved_answer",
    "category",
    "source_type",

]

#Add approved answer manually

def approve_case_manually(
        case_id: str,
        question: str,
        approved_answer: str,
        language: str = "ru",
        category: str = "general",
    ) -> None:

        APPROVED_CASES_PATH.parent.mkdir(parents = True, exist_ok = True)

        #check if file exists
        file_exists = APPROVED_CASES_PATH.exists()


        row = {
            "case_id": case_id,
            "language": language,
            "question": question,
            "approved_answer": approved_answer,
            "category": category,
            "source_type": "admin_review",

        }

        #write answer in approved.csv
        with open(APPROVED_CASES_PATH, mode="a", encoding="utf-8-sig", newline="") as file:
            writer = csv.DictWriter(file, fieldnames=APPROVED_FIELDNAMES)

            if not file_exists:
                writer.writeheader()

            writer.writerow(row)


 