"""
Group Q&A logger.

Tracks user questions (text + photo) posted in group chats and
links admin replies to them so they flow into the approved-answers
learning pipeline.

CSV schema  →  data/raw/group_qa.csv
In-memory cache: (chat_id, message_id) → row  (survives bot restarts via CSV reload)
"""

import csv
import logging
from datetime import datetime
from pathlib import Path

from app.learning.review_manager import clean_text, save_approved_case
from app.bot.language import detect_language

log = logging.getLogger("bot")

BASE_DIR = Path(__file__).resolve().parents[2]
GROUP_QA_PATH = BASE_DIR / "data" / "raw" / "group_qa.csv"

FIELDNAMES = [
    "row_id",
    "datetime",
    "chat_id",
    "chat_title",
    "message_id",
    "user_id",
    "username",
    "question_type",    # "text" | "photo"
    "question_text",
    "saved_photo_path",
    "status",           # "pending" | "answered"
    "admin_answer",
    "admin_username",
    "answered_at",
]

# ── in-memory cache: (chat_id, message_id) → row dict ─────────────────────────
_cache: dict[tuple[int, int], dict] = {}
_cache_loaded = False


def _ensure_cache() -> None:
    """Load pending rows from CSV into memory (once per process start)."""
    global _cache_loaded
    if _cache_loaded:
        return
    _cache_loaded = True

    if not GROUP_QA_PATH.exists():
        return

    try:
        with open(GROUP_QA_PATH, encoding="utf-8-sig", newline="") as f:
            for row in csv.DictReader(f, quoting=csv.QUOTE_ALL):
                if row.get("status", "").strip() == "pending":
                    key = (int(row["chat_id"]), int(row["message_id"]))
                    _cache[key] = dict(row)
    except Exception as e:
        log.warning(f"group_qa_logger: could not load cache: {e}")


def _next_row_id() -> str:
    return "gqa_" + datetime.now().strftime("%Y%m%d_%H%M%S_%f")


def _write_row(row: dict) -> None:
    GROUP_QA_PATH.parent.mkdir(parents=True, exist_ok=True)
    file_exists = GROUP_QA_PATH.exists()
    with open(GROUP_QA_PATH, mode="a", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES, quoting=csv.QUOTE_ALL)
        if not file_exists:
            writer.writeheader()
        writer.writerow(row)


def _update_row_status(chat_id: int, message_id: int, updates: dict) -> None:
    """Rewrite the CSV updating matched row(s)."""
    if not GROUP_QA_PATH.exists():
        return
    rows = []
    try:
        with open(GROUP_QA_PATH, encoding="utf-8-sig", newline="") as f:
            reader = csv.DictReader(f, quoting=csv.QUOTE_ALL)
            fieldnames = reader.fieldnames or FIELDNAMES
            for row in reader:
                if (
                    str(row.get("chat_id")) == str(chat_id)
                    and str(row.get("message_id")) == str(message_id)
                ):
                    row.update(updates)
                rows.append(row)

        with open(GROUP_QA_PATH, mode="w", encoding="utf-8-sig", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames, quoting=csv.QUOTE_ALL)
            writer.writeheader()
            writer.writerows(rows)
    except Exception as e:
        log.warning(f"group_qa_logger: update_row failed: {e}")


# ── public API ─────────────────────────────────────────────────────────────────

def save_group_question(
    chat_id: int,
    chat_title: str,
    message_id: int,
    user_id: int,
    username: str,
    question_type: str,         # "text" | "photo"
    question_text: str,
    saved_photo_path: str = "",
) -> str:
    """Log a user question from a group. Returns row_id."""
    _ensure_cache()

    row_id = _next_row_id()
    row = {
        "row_id": row_id,
        "datetime": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "chat_id": chat_id,
        "chat_title": clean_text(chat_title),
        "message_id": message_id,
        "user_id": user_id,
        "username": clean_text(username),
        "question_type": question_type,
        "question_text": clean_text(question_text),
        "saved_photo_path": saved_photo_path,
        "status": "pending",
        "admin_answer": "",
        "admin_username": "",
        "answered_at": "",
    }

    _write_row(row)
    _cache[(chat_id, message_id)] = row
    log.info(f"📝 Группа [{chat_title}]: вопрос сохранён (msg_id={message_id})")
    return row_id


def load_pending_question(chat_id: int, message_id: int) -> dict | None:
    """Return cached pending question or None."""
    _ensure_cache()
    return _cache.get((chat_id, message_id))


def save_admin_answer(
    chat_id: int,
    original_message_id: int,
    admin_user_id: int,
    admin_username: str,
    admin_answer: str,
    question_text: str,
) -> None:
    """
    Link admin reply to the original question.
    Marks row as answered in CSV and saves to approved.csv for learning.
    """
    _ensure_cache()

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    updates = {
        "status": "answered",
        "admin_answer": clean_text(admin_answer),
        "admin_username": clean_text(admin_username),
        "answered_at": now,
    }

    # update CSV
    _update_row_status(chat_id, original_message_id, updates)

    # update cache
    key = (chat_id, original_message_id)
    if key in _cache:
        _cache[key].update(updates)

    log.info(
        f"✅ Группа: ответ администратора @{admin_username} сохранён "
        f"(msg_id={original_message_id})"
    )

    # push into approved learning pipeline
    if question_text.strip() and admin_answer.strip():
        language = detect_language(question_text)
        case_id = f"group_{chat_id}_{original_message_id}"
        save_approved_case(
            case_id=case_id,
            question=question_text,
            approved_answer=admin_answer,
            language=language,
            category="group_admin_reply",
            source_type="group_chat",
            source_id=f"chat_{chat_id}_msg_{original_message_id}",
            status="approved",
            notes=f"Admin @{admin_username} replied in group chat {chat_id}",
        )
        log.info(f"📚 Ответ добавлен в базу знаний (case_id={case_id})")
