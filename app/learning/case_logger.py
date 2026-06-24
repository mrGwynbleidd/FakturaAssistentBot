#saves weak or failed Q&A pairs to needs_review.csv for admin review
#triggered when the answer or context quality falls below thresholds
#used in bot_engine.py steps 3, 4, and 5

#import libs
import csv
from pathlib import Path
from datetime import datetime

#base path
BASE_DIR = Path(__file__).resolve().parents[2]

#path where cases pending admin review are saved
NEEDS_REVIEW_PATH = BASE_DIR / "data" / "learning" / "needs_review.csv"

#csv column names for needs_review.csv
FIELDNAMES = [
    "case_id",
    "datetime",
    "language",
    "question",
    "bot_answer",
    "sources",
    "status",
    "reason",
    "admin_answer",
    "notes",
]

#converts a list of source dicts to a semicolon-separated string for csv storage
#used in save_case_for_review
def format_sources(sources: list[dict] | None) -> str:

    if not sources:
        return ""

    result = []

    for source in sources:
        source_name = source.get("source", "unknown")
        distance = source.get("distance")

        if distance is not None:
             result.append(f"{source_name} | distance = {distance}")
        else:
             result.append(source_name)

    return "; ".join(result)


#generates a unique case id using current timestamp with microseconds
#used in save_case_for_review
def create_case_id() -> str:
    return "case_" + datetime.now().strftime("%Y%m%d_%H%M%S_%f")

#appends a single Q&A case to needs_review.csv with status "needs_review"
#creates the file and writes header if it does not exist
#returns the generated case_id string
#used in bot_engine.process_user_question when review is needed
def save_case_for_review(
        question: str,
        bot_answer: str,
        language: str = "unknown",
        sources: list[dict] | None = None,
        reason: str = "unknown",
        notes: str = "",
    ) -> str:
        
        #create data directory if missing
        NEEDS_REVIEW_PATH.parent.mkdir(parents=True, exist_ok=True)

        file_exists = NEEDS_REVIEW_PATH.exists()

        #check if existing file already has a header row
        has_header = False
        if file_exists:
             with open(NEEDS_REVIEW_PATH, encoding="utf-8-sig", newline="") as file:
                  first_line = file.readline()
                  has_header = "case_id" in first_line

        case_id = create_case_id()

        row = {
             "case_id": case_id,
             "datetime": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
             "language" : language,
             "question": question,
             "bot_answer": bot_answer,
             "sources": format_sources(sources),
             "status": "needs_review",
             "reason": reason,
             "admin_answer": "",
             "notes": notes,
        }

        #append row to csv, writing header first if needed
        with open(NEEDS_REVIEW_PATH, mode="a", encoding="utf-8-sig", newline="") as file:
             writer = csv.DictWriter(file, fieldnames=FIELDNAMES, quoting=csv.QUOTE_ALL)

             if not has_header:
                  writer.writeheader()

             writer.writerow(row)

        return case_id
