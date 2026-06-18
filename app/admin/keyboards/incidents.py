
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

from app.admin.texts import get_admin_text

#match issues
def incident_match_mode(language: str= "ru") -> ReplyKeyboardMarkup:
    
    keyboard =[
        [
            KeyboardButton(text="contains"),
            KeyboardButton(text="all_keywords"),
        ],
        [
            KeyboardButton(text=get_admin_text("btn_cancel", language)),
        ],
    ]

    return ReplyKeyboardMarkup(
        keyboard=keyboard,
        resize_keyboard=True,
    )

#manage issue
def incident_manage_keyboard(language: str = "ru") -> ReplyKeyboardMarkup:

    keyboard = [
        [
            KeyboardButton(text=get_admin_text("btn_active_incidents", language)),
            KeyboardButton(text=get_admin_text("btn_add_incident", language)),
        ],
        [
            KeyboardButton(text=get_admin_text("btn_back", language)),
        ],
    ]

    return ReplyKeyboardMarkup(
        keyboard=keyboard,
        resize_keyboard=True,
    )

#after saving issue

def incident_after_save_keyboard(language: str = "ru") -> ReplyKeyboardMarkup:

    keyboard = [
        [
            KeyboardButton(text=get_admin_text("btn_add_incident", language)),
            KeyboardButton(text=get_admin_text("btn_active_incidents", language)),
        ],
        [
            KeyboardButton(text=get_admin_text("btn_back", language)),
        ],
    ]

    return ReplyKeyboardMarkup(
        keyboard=keyboard,
        resize_keyboard=True,
    )
