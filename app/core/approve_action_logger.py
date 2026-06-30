# logs approve actions to data/logs/approved_actions.csv
# called from review_service.approve_review_case after saving to approved.csv and updating index
# used for QA, audit trail, and debugging approve pipeline

import csv
from datetime import datetime
from pathlib import Path
from typing import Any

BASE_DIR = Path(__file__).resolve().parents[2]
LOGS_DIR = BASE_DIR / "data" / "logs"
APPROVED_ACTIONS_LOG_PATH = LOGS_DIR / "approved_actions.csv"

FIELDNAMES = [
    "datetime",
    "admin_id",
    "admin_username",
    "review_case_id",
    "question",
    "approved_answer",
    "source_type",
    "source_id",
    "action",
    "approved_csv_written",
    "index_updated",
    "status",
    "error",
]


def _clean(value: Any, limit: int = 700) -> str:
    if value is None:
        return ""
    text = " ".join(str(value).replace("\x00", " ").split())
    if len(text) > limit:
        return text[:limit] + "...[cut]"
    return text


def _ensure_log() -> None:
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    if APPROVED_ACTIONS_LOG_PATH.exists() and APPROVED_ACTIONS_LOG_PATH.stat().st_size > 0:
        return
    with open(APPROVED_ACTIONS_LOG_PATH, mode="w", encoding="utf-8-sig", newline="") as f:
        csv.DictWriter(f, fieldnames=FIELDNAMES).writeheader()


def log_approve_action(
    admin_id: int | str | None,
    admin_username: str | None,
    review_case_id: str,
    question: str,
    approved_answer: str,
    source_type: str = "admin_review",
    source_id: str = "",
    action: str = "approve",
    approved_csv_written: bool = False,
    index_updated: bool = False,
    status: str = "ok",
    error: str = "",
) -> None:
    _ensure_log()
    row = {
        "datetime": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "admin_id": _clean(admin_id, 50),
        "admin_username": _clean(admin_username, 100),
        "review_case_id": _clean(review_case_id, 150),
        "question": _clean(question, 700),
        "approved_answer": _clean(approved_answer, 700),
        "source_type": _clean(source_type, 100),
        "source_id": _clean(source_id, 150),
        "action": _clean(action, 50),
        "approved_csv_written": str(approved_csv_written),
        "index_updated": str(index_updated),
        "status": _clean(status, 50),
        "error": _clean(error, 500),
    }
    with open(APPROVED_ACTIONS_LOG_PATH, mode="a", encoding="utf-8-sig", newline="") as f:
        csv.DictWriter(f, fieldnames=FIELDNAMES).writerow(row)
