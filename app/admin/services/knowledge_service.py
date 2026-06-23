
import csv
from pathlib import Path
from datetime import datetime

from app.admin.services.admin_access import log_admin_action

BASE_DIR = Path(__file__).resolve().parents[3]

ADMIN_DATA_DIR = BASE_DIR / "data" / "admin"
ADMIN_KNOWLEDGE_PATH = ADMIN_DATA_DIR / "admin_knowledge.csv"


KNOWLEDGE_FIELDNAMES = [
    "knowledge_id",
    "datetime",
    "language",
    "question",
    "answer",
    "category",
    "tags",
    "status",
    "created_by",
    "notes",
]

from app.learning.review_manager import clean_text

def create_knowledge_id() -> str:
    return "kb_" + datetime.now().strftime("%Y%m%d_%H%M%S_%f")

def ensure_knowledge_file()-> None:
    ADMIN_DATA_DIR.mkdir(parents=True, exist_ok=True)

    if ADMIN_KNOWLEDGE_PATH.exists():
        return
    
    with open(ADMIN_KNOWLEDGE_PATH, mode="w", encoding="utf-8-sig", newline="",) as f:
        writer = csv.DictWriter(f, fieldnames=KNOWLEDGE_FIELDNAMES, quoting=csv.QUOTE_ALL)
        writer.writeheader()


def read_all_knowledge() -> list[dict]:
    ensure_knowledge_file()

    with open(ADMIN_KNOWLEDGE_PATH, mode="r", encoding="utf-8-sig", newline="",) as f:

        reader = csv.DictReader(f)

        return list(reader)
    
def write_all_knowledge(rows: list[dict]) -> None:

    ADMIN_DATA_DIR.mkdir(parents=True, exist_ok=True)

    with open(ADMIN_KNOWLEDGE_PATH, mode="w", encoding="utf-8-sig", newline="") as f:

        writer = csv.DictWriter(f, fieldnames=KNOWLEDGE_FIELDNAMES, quoting=csv.QUOTE_ALL, extrasaction="ignore",)

        writer.writeheader()
        writer.writerows(rows)

def save_admin_knowledge(
    question: str,
    answer: str,
    language: str = "ru",
    category: str = "general",
    tags: str ="",
    created_by: int | str = "",
    notes: str = "",
    status: str = "approved",
)->str:
    ensure_knowledge_file()

    knowledge_id = create_knowledge_id()

    row = {
        "knowledge_id": knowledge_id,
        "datetime": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "language": clean_text(language),
        "question": clean_text(question),
        "answer": clean_text(answer),
        "category": clean_text(category),
        "tags": clean_text(tags),
        "status": clean_text(status),
        "created_by": clean_text(str(created_by)),
        "notes": clean_text(notes),
    }

    with open(ADMIN_KNOWLEDGE_PATH, mode="a", encoding="utf-8-sig", newline="",) as f:
        writer = csv.DictWriter(f, fieldnames=KNOWLEDGE_FIELDNAMES, quoting=csv.QUOTE_ALL, extrasaction="ignore")

        writer.writerow(row)

    admin_id = int(created_by) if str(created_by).isdigit() else None

    log_admin_action(admin_id=admin_id, action="create_admin_knowledge", details=f"{knowledge_id}: {question[:100]}",)

    return knowledge_id

def list_admin_knowledge(
        status: str | None = None,
        limit: int | None = None,
) -> list[dict]:
    rows = read_all_knowledge()

    if status:
        rows = [
            row for row in rows
            if row.get("status") == status
        ]

    rows = list(reversed(rows))

    if limit:
        return rows[:limit]
    
    return rows


def get_admin_knowledge(knowledge_id: str) -> dict | None:
    rows = read_all_knowledge()

    for row in rows:
        if row.get("knowledge_id") == knowledge_id:
            return row
        
    return None

def update_admin_knowledge_status(
        knowledge_id: str,
        status: str,
        admin_id: int | None = None,
)-> bool:
    rows = read_all_knowledge()
    updated = False

    for row in rows:
        if row.get("knowledge_id") == knowledge_id:
            row["status"] = status
            updated = True
            break

    if not updated:
        return False
    
    write_all_knowledge(rows)

    log_admin_action(admin_id=admin_id,action="update_admin_knowledge_status", details=f"{knowledge_id}: {status}",)

    return True

def disable_admin_knowledge(knowledge_id: str, admin_id: int | None = None,)-> bool:
    return update_admin_knowledge_status(knowledge_id=knowledge_id, status="disabled", admin_id=admin_id,)

