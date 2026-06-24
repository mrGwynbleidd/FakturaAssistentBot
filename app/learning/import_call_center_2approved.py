#imports cleaned call center cases from call_center_cases_raw.csv into approved.csv
#filters out low-quality pairs and optionally auto-approves them
#used as a standalone script to bulk-import call center training data

#import libs
import csv
from pathlib import Path

#import functions
from app.learning.review_manager import save_approved_case
from app.faktura_api.call_center_cleaner import clean_question, clean_answer, is_quality_pair

#base dir
BASE_DIR = Path(__file__).resolve().parents[2]

#path to the raw call center export created by call_center_api.save_callcenter_cases
RAW_CALL_CENTER_PATH = BASE_DIR / "data" / "learning" / "call_center_cases_raw.csv"


#reads call_center_cases_raw.csv, cleans each pair, and saves qualifying ones to approved.csv
#auto_approve must be True to actually write — when False, all rows are counted as skipped
#used as script entry point and from admin import workflows
def import_callcenter_approved(
        min_question_len: int = 10,
        min_answer_len: int = 30,
        auto_approve: bool = False,
) -> None:
    
    if not RAW_CALL_CENTER_PATH.exists():
        print(f"File not found: {RAW_CALL_CENTER_PATH}")
        return
    
    imported = 0
    skipped = 0

    with open(RAW_CALL_CENTER_PATH, mode="r", encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)

        for row in reader:
            raw_question = row.get("question", "").strip()
            raw_answer = row.get("admin_answer", "").strip()
            ticket_id = row.get("case_id", "").strip()
            case_id = row.get("case_id", f"callcenter_{ticket_id}").strip()

            #remove telegram support bot noise from both sides
            question = clean_question(raw_question)
            answer = clean_answer(raw_answer)

            #skip pairs that are too short after cleaning
            if not is_quality_pair(question, answer, min_q=min_question_len, min_a=min_answer_len):
                skipped += 1
                continue

            #when auto_approve is False, skip without saving (dry run mode)
            if not auto_approve:
                skipped += 1
                continue

            save_approved_case(
                case_id=case_id,
                question=question,
                approved_answer=answer,
                language=row.get("language", "ru"),
                category=row.get("category", "call_center"),
                source_type="call_center",
                source_id=ticket_id,
                status="approved",
                notes="Imported from call center API",
            )

            imported +=1

    print(f"Imported: {imported}")
    print(f"Skipped (короткие/пустые): {skipped}")

if __name__ == "__main__":
    import_callcenter_approved(auto_approve=True)
