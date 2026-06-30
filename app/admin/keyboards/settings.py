#settings keyboard — admin management menu
#shown when admin taps the Settings button

from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from app.admin.texts import get_admin_text


def settings_keyboard(language: str = "ru") -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=get_admin_text("btn_list_admins", language))],
            [
                KeyboardButton(text=get_admin_text("btn_add_admin", language)),
                KeyboardButton(text=get_admin_text("btn_remove_admin", language)),
            ],
            [KeyboardButton(text=get_admin_text("btn_back", language))],
        ],
        resize_keyboard=True,
    )
