from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

from app.admin.texts import get_admin_text

def review_action_keyboard(language: str = "ru") -> ReplyKeyboardMarkup:

    keyboard = [
        [
            KeyboardButton(text=get_admin_text("btn_confirm", language)),
            KeyboardButton(text=get_admin_text("btn_reject", language)),
        ],
        [
            KeyboardButton(text=get_admin_text("btn_skip", language)),
            KeyboardButton(text=get_admin_text("btn_cancel", language)),
        ],
    ]

    return ReplyKeyboardMarkup(
        keyboard=keyboard,
        resize_keyboard=True,
    )

def review_after_action_keyboard(language: str = "ru") -> ReplyKeyboardMarkup:

    keyboard = [
        [
            KeyboardButton(text=get_admin_text("btn_review_cases", language)),
            KeyboardButton(text=get_admin_text("btn_back", language)),
        ],
    ]

    return ReplyKeyboardMarkup(
        keyboard=keyboard,
        resize_keyboard=True,
    )

