#manages incidents.csv — create, list, filter, disable, and match active incidents
#incidents are pre-written answers for known active issues that bypass RAG entirely
#used in emergency_answer_checker and admin handlers

import csv
from pathlib import Path
from datetime import datetime

from app.admin.services.admin_access import log_admin_action

BASE_DIR = Path(__file__).resolve().parents[3]

ADMIN_DATA_DIR = BASE_DIR / "data" / "admin"
INCIDENTS_PATH = ADMIN_DATA_DIR / "incidents.csv"

#csv column names for incidents.csv
INCIDENT_FIELDNAMES = [
    "incident_id",
    "datetime",
    "language",
    "title",
    "problem_text",
    "answer",
    "keywords",
    "match_mode",
    "priority",
    "status",
    "start_at",
    "end_at",
    "created_by",
    "notes",
]

from app.learning.review_manager import clean_text

#generates a unique incident id from current timestamp
def create_incident_id() -> str:
    return "inc_" + datetime.now().strftime("%Y%m%d_%H%M%S_%f")

#creates incidents.csv with header if it does not exist
#used before any read or write operation
def ensure_incidents_file() -> None:
    ADMIN_DATA_DIR.mkdir(parents=True, exist_ok=True)

    if INCIDENTS_PATH.exists():
        return
    
    with open(INCIDENTS_PATH, mode="w", encoding="utf-8-sig", newline="",) as f:
        writer = csv.DictWriter(f, fieldnames=INCIDENT_FIELDNAMES, quoting=csv.QUOTE_ALL,)

        writer.writeheader()

#reads all rows from incidents.csv, returns list of row dicts
#used by list_incidents, list_active_incidents, and find_matching_incident
def read_all_incidents() -> list[dict]:
    ensure_incidents_file()

    with open(INCIDENTS_PATH, mode="r", encoding="utf-8-sig", newline="",) as f:
        reader = csv.DictReader(f)
        
        return list(reader)

#overwrites incidents.csv with the given rows list
#used by disable_incident and update_incident_answer after modifying a row in memory
def write_all_incidents(rows: list[dict]) -> None:
    ADMIN_DATA_DIR.mkdir(parents=True, exist_ok=True)

    with open(INCIDENTS_PATH, mode ="w", encoding="utf-8-sig", newline="",) as f:
        writer = csv.DictWriter(f, fieldnames=INCIDENT_FIELDNAMES, quoting=csv.QUOTE_ALL, extrasaction='ignore',)

        writer.writeheader()
        writer.writerows(rows)


#parses a datetime string using multiple formats, returns None if unparseable or explicitly empty
#used in is_incident_time_active to check start_at and end_at
def parse_datetime_or_none(value: str| None) -> datetime | None:

    if value is None: 
        return None
    
    value = str(value).strip()

    if not value:
        return None

    if value.lower() in {"none", "нет", "yoq", "yo'q", "yo'q", "no", "-"}:
        return None
    
    formats = [
        "%Y-%m-%d %H:%M",
        "%Y-%m-%d %H:%M:%S",
        "%d.%m.%Y %H:%M",
    ]

    for date_format in formats:
        try:
            return datetime.strptime(value, date_format)
        except ValueError:
            continue
    
    return None

#saves a new incident row to incidents.csv and logs the admin action
#returns the generated incident_id
#used in incidents_create handler after admin confirms
def save_incident(
        title: str, 
        problem_text: str, 
        answer: str,
        keywords: str,
        language: str = "ru",
        match_mode: str = "contains",
        priority: int = 100,
        start_at: str | None = None,
        end_at: str | None =None,
        created_by: int | str = "",
        notes: str = "",
        status: str = "active"
) -> str:
    
    ensure_incidents_file()

    incident_id = create_incident_id()

    #default start time to now if not provided
    if not start_at:
        start_at = datetime.now().strftime("%Y-%m-%d %H:%M")

    row = {
        "incident_id": incident_id,
        "datetime": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "language": clean_text(language),
        "title": clean_text(title),
        "problem_text": clean_text(problem_text),
        "answer": clean_text(answer),
        "keywords": clean_text(keywords),
        "match_mode": clean_text(match_mode or "contains"),
        "priority": str(priority),
        "status": clean_text(status),
        "start_at": clean_text(start_at),
        "end_at": clean_text(end_at or ""),
        "created_by": clean_text(str(created_by)),
        "notes": clean_text(notes),
    }

    with open(INCIDENTS_PATH, mode="a", encoding="utf-8-sig", newline="",) as f:
        writer = csv.DictWriter(f, fieldnames=INCIDENT_FIELDNAMES, quoting=csv.QUOTE_ALL, extrasaction='ignore')
        writer.writerow(row)

    
    admin_id = int(created_by) if str(created_by).isdigit() else None

    log_admin_action(
        admin_id=admin_id,
        action="create_incident",
        details=f"{incident_id}: {title}",
    )

    return incident_id

#returns a filtered and reversed list of incidents
#status filters by row status field, limit caps the result count
#used in incidents_manage handler and stats_service
def list_incidents(
        status: str | None = None,
        limit: int | None = None,
) -> list[dict]:
    
    rows = read_all_incidents()

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

#returns true if the incident is within its scheduled start/end time window
#used in list_active_incidents
def is_incident_time_active(row: dict) -> bool:
    now = datetime.now()

    start_at = parse_datetime_or_none(row.get("start_at"))
    end_at = parse_datetime_or_none(row.get("end_at"))

    if start_at and now < start_at:
        return False
    
    if end_at and now > end_at:
        return False
    
    return True

#returns active incidents matching the optional language filter, sorted by priority descending
#used in emergency_answer_checker and stats_service
def list_active_incidents(language: str | None = None) -> list[dict]:

    rows = read_all_incidents()
    active_rows = []

    for row in rows:
        if row.get("status") != "active":
            continue

        row_language = row.get("language", "")

        #include incidents for the matching language, "all", or language-unset
        if language and row_language not in {language, "all", ""}:
            continue

        if not is_incident_time_active(row):
            continue

        active_rows.append(row)

    active_rows.sort(
        key=lambda item: int(item.get("priority", "100") or 100),
        reverse=True,
    )

    return active_rows
    

#splits a comma-separated keywords string into a list of lowercase stripped tokens
#used in incident_matches_question
def split_keywords(keywords: str) -> list[str]:
    if not keywords:
        return []
    
    return [
        keyword.strip().lower()
        for keyword in keywords.split(",")
        if keyword.strip()
    ]

#returns true if the question matches the incident keywords according to match_mode
#contains = any keyword present; all_keywords = all keywords must be present
#used in find_matching_incident
def incident_matches_question(row: dict, question: str) -> bool:

    question_lower = question.lower()
    keywords = split_keywords(row.get("keywords", ""))
    match_mode = row.get("match_mode", "contains")

    if not keywords:
        return False
    
    if match_mode == "all_keywords":
        return all(keyword in question_lower for keyword in keywords)
    
    return any(keyword in question_lower for keyword in keywords)

#finds the first active incident that matches the question, returns the row dict or None
#used in emergency_answer_checker.check_active_incidents
def find_matching_incident(question: str, language: str = "ru",) -> dict | None:

    active_incidents = list_active_incidents(language=language)

    for incident in active_incidents:
        if incident_matches_question(incident, question):
            return incident
        
    return None

#sets an incident's status to "disabled" and logs the action, returns True if found
#used in incidents_manage handler disable_incident_command
def disable_incident(
        incident_id: str,
        admin_id: int | None = None,
)-> bool:
    rows = read_all_incidents()
    updated = False

    for row in rows:
        if row.get("incident_id") == incident_id:
            row["status"] = "disabled"
            updated = True
            break

    if not updated:
        return False
    
    write_all_incidents(rows)

    log_admin_action(
        admin_id=admin_id,
        action="disable_incident",
        details=incident_id,
    )

    return True

#updates the answer text for an incident in place and logs the action, returns True if found
#used when admin edits an existing incident answer
def update_incident_answer(
        incident_id: str,
        new_answer: str,
        admin_id: int | None = None,
)-> bool:
    rows = read_all_incidents()
    updated = False

    for row in rows:
        if row.get("incident_id") == incident_id:
            row["answer"] = clean_text(new_answer)
            updated = True
            break

    if not updated:
        return False
    
    write_all_incidents(rows)

    log_admin_action(admin_id=admin_id, action="update incident answer", details=incident_id,)

    return True
