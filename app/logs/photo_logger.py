#import libs
import csv
from pathlib import Path
from datetime import datetime

BASE_DIR = Path(__file__).resolve().parents[2]

PHOTO_LOG_PATH= BASE_DIR / "data" / "raw" / "group_photos.csv"

FIELDNAMES = [
    "datetime",
    "chat_id",
    "chat_title",
    "user_id",
    "username",
    "full_name",
    "message_id",
    "caption",
    "file_id",
    "file_unique_id",
    "saved_path",
]

from app.learning.review_manager import clean_text

def save_photo_log(
        chat_id: int,
        chat_title: str,
        user_id: int,
        username: str,
        fullname: str,
        message_id: int,
        caption: str,
        file_id: str,
        file_unique_id: str,
        saved_path: str,
) -> None:
    
    PHOTO_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)

    file_exists = PHOTO_LOG_PATH.exists()

    row = {
        "datetime": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "chat_id": chat_id,
        "chat_title": clean_text(chat_title),
        "user_id": user_id,
        "username": clean_text(username),
        "full_name": clean_text(fullname),
        "message_id": message_id,
        "caption": clean_text(caption),
        "file_id": file_id,
        "file_unique_id": file_unique_id,
        "saved_path": saved_path,
    }

    with open(PHOTO_LOG_PATH, mode="a", encoding="utf-8-sig",newline="") as file:
        writer = csv.DictWriter(
            file,
            fieldnames=FIELDNAMES,
            quoting=csv.QUOTE_ALL,
        )

        if not file_exists:
            writer.writeheader()

        writer.writerow(row)
