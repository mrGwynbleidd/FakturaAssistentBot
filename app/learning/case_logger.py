#If model not found context or answer is weak save these question to admin review

#import libs
import csv
from pathlib import Path
from datetime import datetime

#base path
BASE_DIR = Path(__file__).resolve().parents[2]

#path where we save question
NEEDS_REVIEW_PATH = BASE_DIR / "data" / "learning" / "needs_review.csv"

#fields for csv
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

#convert list of sources into line
def format_sources(sources: list[dict] | None) -> str:

    #if source is empty
    if not sources:
        return ""

    #arr for new source
    result = []

    for source in sources:
        #get source name
        source_name = source.get("source", "unknown")
        distance = source.get("distance")

        if distance is not None:
             result.append(f"{source_name} | distance = {distance}")

        else:
             result.append(source_name)

    #return arr of soures
    return "; ".join(result)


#create unique id
def create_case_id() -> str:
    return "case_" + datetime.now().strftime("%Y%m%d_%H%M%S_%f")

#save question for review and add admins answer
def save_case_for_review(
        question: str,
        bot_answer: str,
        language: str = "unknown",
        sources: list[dict] | None = None,
        reason: str = "unknown",
        notes: str = "",
    ) -> str:
        
        #create dir if we do not have it
        NEEDS_REVIEW_PATH.parent.mkdir(parents=True, exist_ok=True)

        #check is dir created
        file_exists = NEEDS_REVIEW_PATH.exists()

        #if file exists - check header
        has_header = False
        if file_exists:
             with open(NEEDS_REVIEW_PATH, encoding="utf-8-sig", newline="") as file:
                  first_line = file.readline()
                  has_header = "case_id" in first_line

        #take unique id
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

        #write data in csv
        with open(NEEDS_REVIEW_PATH, mode="a", encoding="utf-8-sig", newline="") as file:
             writer = csv.DictWriter(file, fieldnames=FIELDNAMES, quoting=csv.QUOTE_ALL)

             if not has_header:
                  writer.writeheader()

             writer.writerow(row)

        #return its id
        return case_id     





