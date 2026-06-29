# writes classified tickets to the correct CSV files
# approved    -> data/learning/approved.csv
# needs_review -> data/learning/needs_review.csv
# import_errors -> data/learning/import_errors.csv
# also handles duplicate detection before writing to approved
# used by scripts/import_call_center_tickets.py

import csv
from datetime import datetime
from pathlib import Path
from typing import Any

from app.importers.duplicate_checker import check_duplicate_in_approved, duplicate_result_to_dict
from app.importers.ticket_classifier import (
    DESTINATION_APPROVED,
    DESTINATION_NEEDS_REVIEW,
    DESTINATION_IMPORT_ERRORS,
    TicketClassification,
    classification_to_dict,
)

BASE_DIR = Path(__file__).resolve().parents[2]
LEARNING_DIR = BASE_DIR / "data" / "learning"

APPROVED_CSV_PATH = LEARNING_DIR / "approved.csv"
NEEDS_REVIEW_CSV_PATH = LEARNING_DIR / "needs_review.csv"
IMPORT_ERRORS_CSV_PATH = LEARNING_DIR / "import_errors.csv"

APPROVED_FIELDNAMES = [
    "case_id", "datetime", "language", "question",
    "approved_answer", "category", "source_type", "source_id", "status", "notes",
]

NEEDS_REVIEW_FIELDNAMES = [
    "case_id", "datetime", "language", "question",
    "suggested_answer", "category", "source_type", "source_id", "status", "reasons", "notes",
]

IMPORT_ERRORS_FIELDNAMES = [
    "datetime", "ticket_id", "source_type", "destination",
    "reason", "question", "answer", "category", "status", "raw_payload",
]


# ── helpers ────────────────────────────────────────────────────────────────────

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
        csv.DictWriter(f, fieldnames=fieldnames).writeheader()


# always generates a unique case_id; source_id is embedded if provided for traceability
def make_case_id(source_id: str | None = None) -> str:
    ts = datetime.now().strftime("%Y%m%d%H%M%S%f")
    sid = str(source_id or "").strip()
    if sid:
        return f"cc_{sid}_{ts}"
    return f"cc_{ts}"


# appends one row to the CSV, only writing fields that exist in fieldnames
def append_row(path: Path, fieldnames: list[str], row: dict[str, Any]) -> None:
    ensure_csv_header(path, fieldnames)
    # only keep keys that belong to this file's schema
    safe_row = {field: row.get(field, "") for field in fieldnames}
    with open(path, mode="a", encoding="utf-8-sig", newline="") as f:
        csv.DictWriter(f, fieldnames=fieldnames).writerow(safe_row)


# ── row builders ───────────────────────────────────────────────────────────────

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
) -> dict[str, Any]:
    ticket = classification.normalized_ticket
    return {
        "datetime": now_text(),
        "ticket_id": ticket.get("ticket_id", ""),
        "source_type": "call_center",
        "destination": classification.destination,
        "reason": reason or ";".join(classification.reasons),
        "question": ticket.get("question", ""),
        "answer": ticket.get("answer", ""),
        "category": ticket.get("category", ""),
        "status": ticket.get("status", ""),
        "raw_payload": str(classification_to_dict(classification)),
    }


# ── main write function ────────────────────────────────────────────────────────

# routes the classification to the correct CSV file
# for approved: optionally checks duplicates first and diverts to import_errors if found
# returns a dict describing what was written and where
def write_classified_ticket(
    classification: TicketClassification,
    check_duplicates: bool = True,
) -> dict[str, Any]:

    if classification.destination == DESTINATION_APPROVED:
        if check_duplicates:
            dup = check_duplicate_in_approved(
                ticket=classification.normalized_ticket,
                approved_csv_path=APPROVED_CSV_PATH,
            )
            if dup.is_duplicate:
                dup_info = duplicate_result_to_dict(dup)
                error_row = make_import_error_row(
                    classification=classification,
                    reason=f"skipped_duplicate:{dup.reason}",
                )
                append_row(IMPORT_ERRORS_CSV_PATH, IMPORT_ERRORS_FIELDNAMES, error_row)
                return {
                    "written": False,
                    "destination": "skipped_duplicate",
                    "path": str(IMPORT_ERRORS_CSV_PATH),
                    "reason": dup.reason,
                    "duplicate": dup_info,
                }

        row = make_approved_row(classification)
        append_row(APPROVED_CSV_PATH, APPROVED_FIELDNAMES, row)
        return {
            "written": True,
            "destination": DESTINATION_APPROVED,
            "path": str(APPROVED_CSV_PATH),
            "case_id": row["case_id"],
        }

    if classification.destination == DESTINATION_NEEDS_REVIEW:
        row = make_needs_review_row(classification)
        append_row(NEEDS_REVIEW_CSV_PATH, NEEDS_REVIEW_FIELDNAMES, row)
        return {
            "written": True,
            "destination": DESTINATION_NEEDS_REVIEW,
            "path": str(NEEDS_REVIEW_CSV_PATH),
            "case_id": row["case_id"],
        }

    if classification.destination == DESTINATION_IMPORT_ERRORS:
        row = make_import_error_row(classification)
        append_row(IMPORT_ERRORS_CSV_PATH, IMPORT_ERRORS_FIELDNAMES, row)
        return {
            "written": True,
            "destination": DESTINATION_IMPORT_ERRORS,
            "path": str(IMPORT_ERRORS_CSV_PATH),
            "reason": row["reason"],
        }

    # unknown destination — save as error
    row = make_import_error_row(
        classification=classification,
        reason=f"unknown_destination:{classification.destination}",
    )
    append_row(IMPORT_ERRORS_CSV_PATH, IMPORT_ERRORS_FIELDNAMES, row)
    return {
        "written": True,
        "destination": DESTINATION_IMPORT_ERRORS,
        "path": str(IMPORT_ERRORS_CSV_PATH),
        "reason": row["reason"],
    }


def ensure_learning_csv_files() -> None:
    ensure_csv_header(APPROVED_CSV_PATH, APPROVED_FIELDNAMES)
    ensure_csv_header(NEEDS_REVIEW_CSV_PATH, NEEDS_REVIEW_FIELDNAMES)
    ensure_csv_header(IMPORT_ERRORS_CSV_PATH, IMPORT_ERRORS_FIELDNAMES)
