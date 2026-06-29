
import csv
from datetime import datetime
from pathlib import Path
from typing import Any

BASE_DIR = Path(__file__).resolve().parents[2]

LOGS_DIR = BASE_DIR / "data" / "logs"
ANSWER_MODE_LOG_PATH = LOGS_DIR / "answer_modes.csv"

FIELDNAMES = [
    "datetime",
    "mode",
    "source_type",
    "source_id",
    "score",
    "chat_id",
    "user_id",
    "username",
    "question",
    "answer_preview",
    "matched_question",
    "notes",
]

def clean_text(value: Any, limit: int = 500) -> str:
    if value is None:
        return ""
    
    text = " ".join(str(value).replace("\x00", " ").split())

    if len(text) > limit:
        return text[:limit] + "...[cut]"
    
    return text


def ensure_answer_mode_log() -> None:
    LOGS_DIR.mkdir(parents=True, exist_ok=True)

    if ANSWER_MODE_LOG_PATH.exists() and ANSWER_MODE_LOG_PATH.stat().st_size > 0:
        return
    
    with open(
        ANSWER_MODE_LOG_PATH,
        mode="w",
        encoding="utf-8-sig",
        newline="", 
    ) as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        writer.writeheader()


def log_answer_mode(
        mode: str,
        question: str,
        answer: str = "",
        source_type: str ="",
        source_id: str = "",
        score: float | str = "",
        chat_id: int | str | None = "",
        user_id: int | str | None = "",
        username: str | None = "",
        matched_question: str = "",
        notes: str = "",
)-> None:
    ensure_answer_mode_log()

    row = {
        "datetime": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "mode": clean_text(mode, 100),
        "source_type": clean_text(source_type, 100),
        "source_id": clean_text(source_id, 150),
        "score": clean_text(score, 50),
        "chat_id": clean_text(chat_id, 100),
        "user_id": clean_text(user_id, 100),
        "username": clean_text(username, 150),
        "question": clean_text(question, 700),
        "answer_preview": clean_text(answer, 700),
        "matched_question": clean_text(matched_question, 700),
        "notes": clean_text(notes, 500),
    }

    with open(
        ANSWER_MODE_LOG_PATH,
        mode="a",
        encoding="utf-8-sig",
        newline="",
    ) as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        writer.writerow(row)
