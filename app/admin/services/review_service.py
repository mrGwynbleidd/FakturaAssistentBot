
import csv
from pathlib import Path
from datetime import datetime

from app.admin.services.admin_access import log_admin_action

BASE_DIR = Path(__file__).resolve().parents[3]

NEEDS_REVIEW_PATH = BASE_DIR / "data" / "learning" / "needs_review.csv"

NEEDS_REVIEW_FIELDNAMES = [
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

from app.learning.review_manager import clean_text

def ensure_needs_review_file() -> None:
    NEEDS_REVIEW_PATH.parent.mkdir(parents=True, exist_ok=True)

    if NEEDS_REVIEW_PATH.exists():
        return
    
    with open(NEEDS_REVIEW_PATH, mode="w", encoding="utf-8-sig", newline="",) as f:
        writer = csv.DictWriter(f, fieldnames=NEEDS_REVIEW_FIELDNAMES, quoting=csv.QUOTE_ALL)

        writer.writeheader()


def read_all_review_cases() -> list[dict]:
    ensure_needs_review_file()

    with open(NEEDS_REVIEW_PATH, mode="r", encoding="utf-8-sig", newline="",) as f:
        reader = csv.DictReader(f)

        return list(reader)
    

def write_all_review_cases(rows: list[dict]) -> None:
    NEEDS_REVIEW_PATH.parent.mkdir(parents=True, exist_ok=True)

    with open(NEEDS_REVIEW_PATH, mode="w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=NEEDS_REVIEW_FIELDNAMES, quoting=csv.QUOTE_ALL, extrasaction='ignore')

        writer.writeheader()
        writer.writerows(rows)


def load_review_cases(status: str | None = "needs_review", limit: int | None = None,) -> list[dict]:

    rows = read_all_review_cases()

    if status:
        rows = [
            row for row in rows
            if row.get("status") == status
        ]

    rows = list(reversed(rows))

    if limit:
        return rows[:limit]
    
    return rows

def get_review_case(case_id: str) -> dict | None:
    rows = read_all_review_cases()

    for row in rows:
        if row.get("case_id") == case_id:
            return row
        
    return None

def update_review_case_status(case_id: str, status: str, admin_answer: str = "", notes: str = "",) -> bool:

    rows = read_all_review_cases()
    updated = False

    for row in rows:
        if row.get("case_id") == case_id:
            row["status"] = status

            if admin_answer:
                row["admin_answer"] = clean_text(admin_answer)

            if notes:
                row["notes"] = clean_text(notes)

            
            updated = True
            break

    if not updated:
        return False
    
    write_all_review_cases(rows)

    return True


def save_to_approved_cases(
        case_id: str,
        question: str,
        approved_answer: str,
        language: str = "ru",
        category: str = "review",
        source_type: str = "admin_review",
        source_id: str = "",
        notes: str = "",
) -> None:
    from app.learning.review_manager import save_approved_case

    save_approved_case(
        case_id=case_id,
        question=question,
        approved_answer=approved_answer,
        language=language,
        category=category,
        source_type=source_type,
        source_id=source_id or case_id,
        status="approved",
        notes=notes,
    )

    
    try:
        from app.rag.approved_index_updater import add_approved_case_to_index
        add_approved_case_to_index(
        case_id=case_id,
        question=question,
        answer=approved_answer,
        language=language,
        category=category,
        source_type="admin_review",
        source_id=case_id,
        )
    except Exception as err:
        print("Approved case saved to CSV, but index update failed:", err)
    

#########



def approve_review_case(
        case_id: str,
        admin_answer: str,
        admin_id: int | None = None,
        category: str = "review",
) -> bool:
    case = get_review_case(case_id)

    if not case:
        return False
    
    question = case.get("question", "")
    language = case.get("language", "ru")

    save_to_approved_cases(
        case_id=case_id,
        question=question,
        approved_answer=admin_answer,
        language=language,
        category=category,
        source_type="admin_review",
        source_id=case_id,
        notes=f"Approved from review by admin {admin_id} at {datetime.now()}",
    )

    updated = update_review_case_status(
        case_id=case_id,
        status="approved",
        admin_answer=admin_answer,
        notes=f"Approved by admin {admin_id}",
    )

    if updated:
        log_admin_action(
            admin_id=admin_id,
            action="approve_review_case",
            details=case_id,
        )
    return updated


def reject_review_case(
        case_id: str,
        admin_id: int | None = None,
        notes: str = "",
) -> bool:
    updated = update_review_case_status(
        case_id=case_id,
        status="rejected",
        notes=notes or f"Rejected by admin {admin_id}",
    )

    if updated:
        log_admin_action(
            admin_id=admin_id,
            action="reject_review_case",
            details=case_id,
        )
    
    return updated


def count_review_cases() -> dict:
    rows = read_all_review_cases()

    result = {
        "needs_review": 0,
        "approved": 0,
        "rejected": 0,
        "other": 0,
    }

    for row in rows:
        status = row.get("status", "other")

        if status in result:
            result[status] +=1
        else:
            result["other"] +=1

    return result
 
