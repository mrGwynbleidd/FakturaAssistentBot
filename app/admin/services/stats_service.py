#collects and formats bot statistics from all csv data files
#used in admin stats handler to show counts to the admin

import csv
from pathlib import Path

from app.admin.services.incident_service import list_active_incidents
from app.admin.services.review_service import count_review_cases

BASE_DIR = Path(__file__).resolve().parents[3]

#paths to all tracked data files
QA_OUTPUTS_PATH = BASE_DIR / "data" / "raw" / "QA_outputs.csv"
GROUP_PHOTOS_LOG_PATH = BASE_DIR / "data" / "raw" / "group_photos.csv"
ADMIN_KNOWLEDGE_PATH = BASE_DIR / "data" / "admin" / "admin_knowledge.csv"
INCIDENTS_PATH = BASE_DIR / "data" / "admin" / "incidents.csv"


#counts data rows in a csv file, returns 0 if file does not exist
#used in get_bot_stats to count records in each file
def count_csv_rows(path: Path) -> int:
    if not path.exists():
        return 0
    
    with open(path, mode="r", encoding="utf-8-sig", newline="") as f:

        reader =csv.DictReader(f)
        return sum(1 for _ in reader)
    
#builds a stats dict with counts from all relevant csv files and review case breakdown
#used in format_stats_text
def get_bot_stats() -> dict:
    review_counts = count_review_cases()
    active_incidents = list_active_incidents()

    return {
        "qa_outputs_count": count_csv_rows(QA_OUTPUTS_PATH),
        "group_photos_count": count_csv_rows(GROUP_PHOTOS_LOG_PATH),
        "admin_knowledge_count": count_csv_rows(ADMIN_KNOWLEDGE_PATH),
        "incidents_count": count_csv_rows(INCIDENTS_PATH),
        "active_incidents_count": len(active_incidents),
        "review_needs_count": review_counts.get("needs_review", 0),
        "review_approved_count": review_counts.get("approved", 0),
        "review_rejected_count": review_counts.get("rejected", 0),
    }


#formats the stats dict into a human-readable text block in the given language
#used in admin stats handler to send statistics message
def format_stats_text(language: str = "ru") -> str:
    stats = get_bot_stats()

    if language == "en":
        return (
             "📊 Bot statistics\n\n"
            f"Questions saved: {stats['qa_outputs_count']}\n"
            f"Saved group photos: {stats['group_photos_count']}\n"
            f"Admin Q/A: {stats['admin_knowledge_count']}\n"
            f"Temporary issues total: {stats['incidents_count']}\n"
            f"Active issues: {stats['active_incidents_count']}\n"
            f"Cases waiting for review: {stats['review_needs_count']}\n"
            f"Approved cases: {stats['review_approved_count']}\n"
            f"Rejected cases: {stats['review_rejected_count']}"
        )
    
    if language == "uz":
        return (
            "📊 Bot statistikasi\n\n"
            f"Saqlangan savollar: {stats['qa_outputs_count']}\n"
            f"Saqlangan guruh rasmlari: {stats['group_photos_count']}\n"
            f"Admin Q/A: {stats['admin_knowledge_count']}\n"
            f"Vaqtinchalik muammolar jami: {stats['incidents_count']}\n"
            f"Faol muammolar: {stats['active_incidents_count']}\n"
            f"Tekshiruv kutayotgan keyslar: {stats['review_needs_count']}\n"
            f"Tasdiqlangan keyslar: {stats['review_approved_count']}\n"
            f"Rad etilgan keyslar: {stats['review_rejected_count']}"
        )

    return (
        "📊 Статистика бота\n\n"
        f"Сохранённых вопросов: {stats['qa_outputs_count']}\n"
        f"Сохранённых фото из группы: {stats['group_photos_count']}\n"
        f"Ручных Q/A от админа: {stats['admin_knowledge_count']}\n"
        f"Временных проблем всего: {stats['incidents_count']}\n"
        f"Активных проблем: {stats['active_incidents_count']}\n"
        f"Кейсов на проверке: {stats['review_needs_count']}\n"
        f"Одобренных кейсов: {stats['review_approved_count']}\n"
        f"Отклонённых кейсов: {stats['review_rejected_count']}"
    )
