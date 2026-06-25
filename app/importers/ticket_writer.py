
import csv
from datetime import datetime
from pathlib import Path
from typing import Any

from app.importers.duplicate_checker import check_duplicate_in_approved, duplicate_result_to_dict

from app.importers.ticket_classifier import DESTINATION_APPROVED, DESTINATION_NEEDS_REVIEW, DESTINATION_IMPORT_ERRORS, TicketClassification, classification_to_dict

BASE_DIR = Path(__file__).resolve().parents[2]

LEARNING_DIR = BASE_DIR / "data" / "learning"

APPROVED_CSV_PATH = LEARNING_DIR / "approved.csv"
NEEDS_REVIEW_CSV_PATH = LEARNING_DIR / "needs_review.csv"
IMPORT_ERRORS_CSV_PATH = LEARNING_DIR / "import_errors.csv"

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

NEEDS_REVIEW_FIELDNAMES = [
    "case_id",
    "datetime",
    "language",
    "question",
    "suggested_answer",
    "category",
    "source_type",
    "source_id",
    "status",
    "reasons",
    "notes",
]


IMPORT_ERRORS_FIELDNAMES = [
    "datetime",
    "ticket_id",
    "source_type",
    "destination",
    "reason",
    "question",
    "answer",
    "category",
    "status",
    "raw_payload",
]

def ensure_learning_dir() -> None:
    LEARNING_DIR.mkdir(parents=True, exist_ok=True)

def now_text() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def file_is_empty(path: Path) -> bool:
    return not path.exists() or path.stat().st_size == 0

def ensure_csv_header(path: Path, fieldnames: list[str]) -> None:

    ensure_learning_dir()

    if not file_is_empty(path):
        return
    
    with open(path, mode="w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)

        writer.writeheader()



def append_row(path: Path, fieldnames: list[str], row: dict[str, Any]) -> None:


    ensure_csv_header(path, fieldnames)

    safe_row = {
        fieldname: row.get(fieldname, "")
        for fieldname in fieldnames 
    }

    with open(path, mode="a", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writerow(row)


def make_case_id(source_id: str | None) -> str:
    source_id = str(source_id or "").strip()

    if source_id:
        return f"call_import_{datetime.now().strftime('%Y%m%d%H%M%S%f')}"
    
def make_approved_row(classification: TicketClassification) -> dict[str, Any]:
    ticket = classification.normalized_ticket
    ticket_id = ticket.get("ticket_id", "")


    return {
        "case_id": make_case_id(ticket_id),
        "datetime": ticket.get("created_at") or now_text(),
        "language": ticket.get("language", "ru"),
        "question": ticket.get("question", ""),
        "approved_answer": ticket.get("answer", ""),
        "category": ticket.get("category", "general"),
        "source_type": "call_center",
        "source_id": ticket_id,
        "status": "approved",
        "notes": "Imported from call center",
    }

def make_needs_review_row(classification: TicketClassification) -> dict[str, Any]:
    ticket = classification.normalized_ticket
    ticket_id = ticket.get("ticket_id", "")

    return {
        "case_id": make_case_id(ticket_id),
        "datetime": ticket.get("created_at") or now_text(),
        "language": ticket.get("language", "ru"),
        "question": ticket.get("question", ""),
        "suggested_answer": ticket.get("answer", ""),
        "category": ticket.get("category", "general"),
        "source_type": "call_center",
        "source_id": ticket_id,
        "status": "needs_review",
        "reasons": ";".join(classification.reasons),
        "notes": "Imported from call center. Requires admin review.",
    }

def make_import_error_row(
    classification: TicketClassification,
    reason: str | None = None,
    raw_payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    ticket = classification.normalized_ticket
    reasons = reason or ";".join(classification.reasons)

    return {
        "datetime": now_text(),
        "ticket_id": ticket.get("ticket_id", ""),
        "source_type": "call_center",
        "destination": classification.destination,
        "reason": reasons,
        "question": ticket.get("question", ""),
        "answer": ticket.get("answer", ""),
        "category": ticket.get("category", ""),
        "status": ticket.get("status", ""),
        "raw_payload": str(raw_payload or classification_to_dict(classification)),
    }


def write_classified_ticket(
        classification: TicketClassification,
        check_duplicates: bool = True,
)-> dict[str, Any]:
    
    if classification.destination == DESTINATION_APPROVED:
        if check_duplicates:
            duplicate_result = check_duplicate_in_approved(
                ticket=classification.normalized_ticket,
                approved_csv_path=APPROVED_CSV_PATH,
            )

            if duplicate_result.is_duplicate:
                duplicate_info = duplicate_result_to_dict(duplicate_result)
                error_row = make_approved_row(
                    classification=classification,
                    reason=f"skipped_duplicate:{duplicate_info}",
                )

                append_row(
                    path=IMPORT_ERRORS_CSV_PATH,
                    fieldnames=IMPORT_ERRORS_FIELDNAMES,
                    row=error_row,
                )

                return {
                    "written": False,
                    "destination": "skipped_duplicates",
                    "path": str(IMPORT_ERRORS_CSV_PATH),
                    "reason": duplicate_result.reason,
                    "duplicate": duplicate_info,
                }
            
            row = make_approved_row(classification)

            append_row(
                path=APPROVED_CSV_PATH,
                fieldnames=APPROVED_FIELDNAMES,
                row=row,
            )

            return {
                "written": True,
                "destination": DESTINATION_APPROVED,
                "path": str(APPROVED_CSV_PATH),
                "case_id": row["case_id"],
            }
        
    if classification.destination == DESTINATION_NEEDS_REVIEW:
        row = make_needs_review_row(classification)

        append_row(
            path=NEEDS_REVIEW_CSV_PATH,
            fieldnames=NEEDS_REVIEW_FIELDNAMES,
            row=row,
        )

        return {
            "written": True,
            "destination": DESTINATION_NEEDS_REVIEW,
            "path": str(NEEDS_REVIEW_CSV_PATH),
            "case_id": row["case_id"],
        }

    if classification.destination == DESTINATION_IMPORT_ERRORS:
        row = make_import_error_row(classification)

        append_row(
            path=IMPORT_ERRORS_CSV_PATH,
            fieldnames=IMPORT_ERRORS_FIELDNAMES,
            row=row,
        )

        return {
            "written": True,
            "destination": DESTINATION_IMPORT_ERRORS,
            "path": str(IMPORT_ERRORS_CSV_PATH),
            "reason": row["reason"],
        }
    
    row = make_import_error_row(
        classification=classification,
        reason=f"unknown_destination:{classification:destination}",
    )

    append_row(
        path=IMPORT_ERRORS_CSV_PATH,
        fieldnames=IMPORT_ERRORS_FIELDNAMES,
        row=row,
    )

    return {
        "written": True,
        "destination": DESTINATION_IMPORT_ERRORS,
        "path": str(IMPORT_ERRORS_CSV_PATH),
        "reason": row["reason"],
    }


def ensure_learning_csv_files() -> None:
    """
    Creates all target CSV files with headers if they do not exist.
    """

    ensure_csv_header(APPROVED_CSV_PATH, APPROVED_FIELDNAMES)
    ensure_csv_header(NEEDS_REVIEW_CSV_PATH, NEEDS_REVIEW_FIELDNAMES)
    ensure_csv_header(IMPORT_ERRORS_CSV_PATH, IMPORT_ERRORS_FIELDNAMES)


