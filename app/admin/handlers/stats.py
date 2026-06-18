
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message

from app.admin.services.admin_access import is_admin, get_admin_language
from app.admin.services.stats_service import format_stats_text
from app.admin.texts import get_admin_text
from app.admin.keyboards.main import admin_main_keyboard

router = Router(name="admin_stats")

def text_values(key: str) -> list[str]:

    values = [
        get_admin_text(key, "ru"),
        get_admin_text(key, "uz"),
        get_admin_text(key, "en"),
        key,
    ]

    aliases = {
        "btn_stats": [
            "stats",
            "statistika",
            "статистика",
            "btn_stats",
            "📊 Статистика",
        ],
    }

    values.extend(aliases.get(key, []))


    return list(set(values))
    

@router.message(Command("admin_stats"))
async def admin_stats(message: Message):
    if not is_admin(message.from_user.id if message.from_user else None):
        return
    
    language = get_admin_language(message.from_user.id if message.from_user else None)

    await message.answer(
        format_stats_text(language),
        reply_markup=admin_main_keyboard(language),
    )
