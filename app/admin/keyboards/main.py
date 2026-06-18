from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

from app.admin.texts import get_admin_text

def admin_main_keyboard(language: str = "ru") -> ReplyKeyboardMarkup:
    keyboard = [
        [
            KeyboardButton(text=get_admin_text("btn_add_qa", language)),
            KeyboardButton(text=get_admin_text("btn_add_incident", language)),
        ],
        [
            KeyboardButton(text=get_admin_text("btn_active_incidents", language)),
            KeyboardButton(text=get_admin_text("btn_review_cases", language)),
        ],
        [
            KeyboardButton(text=get_admin_text("btn_read_only", language)),
        ],
        [
            KeyboardButton(text=get_admin_text("btn_stats", language)),
            KeyboardButton(text=get_admin_text("btn_settings", language)),
        ],
        [
            KeyboardButton(text=get_admin_text("btn_exit", language)),
        ],
    ]

    return ReplyKeyboardMarkup(
        keyboard=keyboard,
        resize_keyboard=True,
    )



def admin_cancel_keyboard(language: str = "ru") -> ReplyKeyboardMarkup:

    keyboard = [
        [
            KeyboardButton(text=get_admin_text("btn_cancel", language)),
        ],
    ]

    return ReplyKeyboardMarkup(
        keyboard=keyboard,
        resize_keyboard=True,
    )

def admin_confirm_keyboard(language: str = "ru") -> ReplyKeyboardMarkup:
    
    keyboard = [
        [
            KeyboardButton(text=get_admin_text("btn_confirm", language)),
            KeyboardButton(text=get_admin_text("btn_cancel", language)),
        ],
    ]

    return ReplyKeyboardMarkup(
        keyboard=keyboard,
        resize_keyboard=True,
    )



