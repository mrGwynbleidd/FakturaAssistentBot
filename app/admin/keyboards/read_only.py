
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

from app.admin.texts import get_admin_text

def read_only_keyboard(language: str = "ru") -> ReplyKeyboardMarkup:
    keyboard = [
        [
            KeyboardButton(text=get_admin_text("btn_read_only_all", language)),
        ],
        [
            KeyboardButton(text=get_admin_text("btn_read_only_selected", language)),
        ],
        [
            KeyboardButton(text=get_admin_text("btn_read_only_off", language)),
        ],
        [
            KeyboardButton(text=get_admin_text("btn_read_only_add_current_chat", language)),
            KeyboardButton(text=get_admin_text("btn_read_only_remove_current_chat", language)),
        ],
        [
            KeyboardButton(text=get_admin_text("btn_read_only_list_chats", language)),
        ],
        [
            KeyboardButton(text=get_admin_text("btn_back", language)),
        ],
    ]

    return ReplyKeyboardMarkup(
        keyboard=keyboard,
        resize_keyboard=True,
    )



