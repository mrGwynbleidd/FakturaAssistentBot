# keyboard for the read-only panel in admin chat
# shows mode selector and back button
# adding/removing chats is done via /readonly command in the group itself

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
            KeyboardButton(text=get_admin_text("btn_back", language)),
        ],
    ]
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)
