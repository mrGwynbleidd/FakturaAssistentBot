#Add correct answer

#import libs
import csv
from pathlib import Path
from datetime import datetime

#base path
BASE_DIR = Path(__file__).resolve().parents[2]

#path where bad answer stored for now not used
NEEDS_REVIEW_PATH = BASE_DIR / "data" / "learning" / "needs_review.csv"
#path where correct answer will be saved
APPROVED_CASES_PATH = BASE_DIR / "data" / "learning" / "approved.csv"

#fieldnames for csv
APPROVED_FIELDNAMES = [
    "case_id",
    "datetime",
    "language",
    "question",
    "approved_answer",
    "category",
    "source_type",
    "source_id",
    "status",
    "notes",

]

#clean text for csv
def clean_text(value: str | None) -> str:
     
     if not value:
          return " "
     
     return " ".join(str(value).split())


#check header csv
#if header is wrong, recreate file

def ensure_csv_header(path: Path, fieldnames: list[str]) -> None:
     
    path.parent.mkdir(parents=True, exist_ok=True)
    
    if not path.exists():
        return

    with open(path, mode="r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)

        cur_header = next(reader, [])

    if cur_header != fieldnames:
         backup_path = path.with_name(
              f"{path.stem}_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}{path.suffix}"
         )

         path.rename(backup_path)
         print(f"Old approved.csv header was wrong. Backup created: {backup_path}")


#save approved cases, will use in ChromaDB
def save_approved_case(
          case_id: str,
          question: str,
          approved_answer: str,
          language: str = "ru",
          category: str = "general",
          source_type: str = "admin_review",
          source_id: str = "",
          status:  str = "approved",
          notes: str = "",
)-> None:
     
    ensure_csv_header(APPROVED_CASES_PATH, APPROVED_FIELDNAMES)

    file_exists = APPROVED_CASES_PATH.exists()

    row = {
         "case_id": clean_text(case_id),
         "datetime": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
         "language": clean_text(language),
         "question": clean_text(question),
         "approved_answer": clean_text(question),
         "category": clean_text(category),
         "source_type": clean_text(source_type),
         "source_id": clean_text(source_id),
         "status": clean_text(status),
         "notes": clean_text(notes),
    }

    with open(APPROVED_CASES_PATH, mode="a", encoding="utf-8-sig", newline="") as file:
        writer = csv.DictWriter(
            file,
            fieldnames=APPROVED_FIELDNAMES,
            quoting=csv.QUOTE_ALL,
            extrasaction="ignore",
        )

        if not file_exists:
            writer.writeheader()

        writer.writerow(row)
       


#Add approved answer manually
#for test
def approve_case_manually(
        case_id: str,
        question: str,
        approved_answer: str,
        language: str = "ru",
        category: str = "general",
    ) -> None:

        save_approved_case(
             case_id=case_id,
             question=question,
             approved_answer=approved_answer,
             language=language,
             category=category,
             source_type="admin_review",
             source_id=case_id,
             status="approved",
        )

 