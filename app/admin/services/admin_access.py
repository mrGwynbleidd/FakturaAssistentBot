#provides admin access checks and logs admin actions to a csv audit log
#used by all admin handlers to verify permissions and record activity

import csv
from pathlib import Path
from datetime import datetime

from app.admin.admin_config import is_admin_user

BASE_DIR = Path(__file__).resolve().parents[3]

ADMIN_DATA_DIR= BASE_DIR / "data" / "admin"
ADMIN_ACTIONS_LOG_PATH = ADMIN_DATA_DIR / "admin_action_log.csv"

#csv column names for admin action log
ADMIN_ACTION_FIELDNAMES = [
    "datetime",
    "admin_id",
    "action",
    "details",
]

#returns true if user_id belongs to an admin, delegates to admin_config.is_admin_user
#used in all admin handlers as access guard
def is_admin(user_id: int | None) -> bool:
    return is_admin_user(user_id)

#returns the preferred language for an admin — currently always ru
#placeholder for future per-admin language preference
def get_admin_language(user_id: int | None) -> str:
    return "ru"

from app.learning.review_manager import clean_text

#ensures the admin action log csv file exists with the correct header
#creates parent directories and writes header if file is missing
def ensure_admin_log_file() -> None:
    ADMIN_DATA_DIR.mkdir(parents=True, exist_ok=True)

    if ADMIN_ACTIONS_LOG_PATH.exists():
        return
    
    with open(ADMIN_ACTIONS_LOG_PATH, mode="w", encoding="utf-8-sig", newline="",) as file:
        writer = csv.DictWriter(file, fieldnames=ADMIN_ACTION_FIELDNAMES, quoting=csv.QUOTE_ALL,)

        writer.writeheader()


#appends a single admin action row to admin_action_log.csv
#used throughout admin services to record approve, reject, create, and update actions
def log_admin_action(
        admin_id: int | None,
        action: str,
        details: str = "",
)-> None:
    ensure_admin_log_file()

    row = {
        "datetime": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "admin_id": admin_id or "",
        "action": clean_text(action),
        "details": clean_text(details),
    }

    with open(ADMIN_ACTIONS_LOG_PATH, mode='a', encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=ADMIN_ACTION_FIELDNAMES, quoting=csv.QUOTE_ALL,)

        writer.writerow(row)
