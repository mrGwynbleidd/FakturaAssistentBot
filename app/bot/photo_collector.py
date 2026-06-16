
from pathlib import Path
from datetime import datetime

from aiogram.types import Message

from app.config import GROUP_PHOTO_SAVE_DIR
from app.logs.photo_logger import save_photo_log

BASE_DIR = Path(__file__).resolve().parents[2]

def build_user_full_name(message: Message) -> str:
    if not message.from_user:
        return ""
    
    firstname = message.from_user.first_name or ""
    lastname = message.from_user.last_name or ""

    return f"{firstname} {lastname}".strip()

async def save_group_photo(message: Message) -> str | None:

    if not message.photo:
        return None
    
    largest_photo = message.photo[-1]

    chat_id = message.chat.id
    user_id = message.from_user.id if message.from_user else 0

    date_folder = datetime.now().strftime("%Y-%m-%d")

    save_dir = BASE_DIR / GROUP_PHOTO_SAVE_DIR / date_folder
    save_dir.mkdir(parents=True, exist_ok=True)

    username = message.from_user.username if message.from_user and message.from_user.username else ""
    fullname = build_user_full_name(message)

    filename = (
        f"{datetime.now().strftime("%H%M%S")}_"
        f"chat_{chat_id}_"
        f"user_{user_id}_"
        f"msg_{message.message_id}_"
        f"{largest_photo.file_unique_id}.jpg"

    )


    save_path =save_dir / filename

    await message.bot.download(
        largest_photo,
        destination=save_path,
    )

    save_photo_log(
        chat_id=chat_id,
        chat_title=message.chat.title or "",
        user_id=user_id,
        username=username,
        fullname=fullname,
        message_id=message.message_id,
        caption=message.caption or "",
        file_id=largest_photo.file_id,
        file_unique_id=largest_photo.file_unique_id,
        saved_path=str(save_path),
    )

    return str(save_path)