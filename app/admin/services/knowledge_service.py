#manages admin_knowledge.csv — create, list, fetch, and disable admin Q&A entries
#admin knowledge is the highest-priority source in the RAG pipeline
#used in knowledge_create handler and admin_knowledge_loader

import csv
from pathlib import Path
from datetime import datetime

from app.admin.services.admin_access import log_admin_action

BASE_DIR = Path(__file__).resolve().parents[3]

ADMIN_DATA_DIR = BASE_DIR / "data" / "admin"
ADMIN_KNOWLEDGE_PATH = ADMIN_DATA_DIR / "admin_knowledge.csv"

#csv column names for admin_knowledge.csv
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

#generates a unique knowledge id from current timestamp
def create_knowledge_id() -> str:
    return "kb_" + datetime.now().strftime("%Y%m%d_%H%M%S_%f")

#ensures admin_knowledge.csv exists with header, creates parent directories if needed
def ensure_knowledge_file()-> None:
    ADMIN_DATA_DIR.mkdir(parents=True, exist_ok=True)

    if ADMIN_KNOWLEDGE_PATH.exists():
        return
    
    with open(ADMIN_KNOWLEDGE_PATH, mode="w", encoding="utf-8-sig", newline="",) as f:
        writer = csv.DictWriter(f, fieldnames=KNOWLEDGE_FIELDNAMES, quoting=csv.QUOTE_ALL)
        writer.writeheader()


#reads all rows from admin_knowledge.csv, returns list of row dicts
#used by list_admin_knowledge, get_admin_knowledge, and update_admin_knowledge_status
def read_all_knowledge() -> list[dict]:
    ensure_knowledge_file()

    with open(ADMIN_KNOWLEDGE_PATH, mode="r", encoding="utf-8-sig", newline="",) as f:

        reader = csv.DictReader(f)

        return list(reader)

#overwrites admin_knowledge.csv with the given rows list
#used after modifying a row status in memory
def write_all_knowledge(rows: list[dict]) -> None:

    ADMIN_DATA_DIR.mkdir(parents=True, exist_ok=True)

    with open(ADMIN_KNOWLEDGE_PATH, mode="w", encoding="utf-8-sig", newline="") as f:

        writer = csv.DictWriter(f, fieldnames=KNOWLEDGE_FIELDNAMES, quoting=csv.QUOTE_ALL, extrasaction="ignore",)

        writer.writeheader()
        writer.writerows(rows)

#appends a new Q&A entry to admin_knowledge.csv and logs the admin action
#returns the generated knowledge_id
#used in knowledge_create handler after admin confirms
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

#returns a filtered and reversed list of admin knowledge entries
#status filters by row status field, limit caps the result count
#used in admin knowledge list views
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

    #newest first
    rows = list(reversed(rows))

    if limit:
        return rows[:limit]
    
    return rows


#returns a single knowledge entry by knowledge_id, or None if not found
#used when looking up a specific entry for update or disable
def get_admin_knowledge(knowledge_id: str) -> dict | None:
    rows = read_all_knowledge()

    for row in rows:
        if row.get("knowledge_id") == knowledge_id:
            return row
        
    return None

#sets a knowledge entry's status field and logs the action, returns True if found
#used in disable_admin_knowledge
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

#convenience wrapper that disables a knowledge entry by setting status to "disabled"
#used in admin knowledge management
def disable_admin_knowledge(knowledge_id: str, admin_id: int | None = None,)-> bool:
    return update_admin_knowledge_status(knowledge_id=knowledge_id, status="disabled", admin_id=admin_id,)
