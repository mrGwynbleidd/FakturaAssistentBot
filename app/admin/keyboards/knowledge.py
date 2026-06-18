from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

from app.admin.texts import get_admin_text

#add manual q/a
def knowledge_category_keyboard(language: str = "ru") -> ReplyKeyboardMarkup:

    keyboard = [
        [
            KeyboardButton(text="login"),
            KeyboardButton(text="documents"),
        ],
        [
            KeyboardButton(text="soliq"),
            KeyboardButton(text="api"),
        ],
        [
            KeyboardButton(text="general"),
            KeyboardButton(text=get_admin_text("btn_cancel")),
        ],
    ]

    return ReplyKeyboardMarkup(
        keyboard=keyboard,
        resize_keyboard=True,
    )

#after saving q/a
def knowledge_after_save_keyboard(language: str = "ru") -> ReplyKeyboardMarkup:

    keyboard = [
        [
            KeyboardButton(text=get_admin_text("btn_add_qa", language)),
            KeyboardButton(text=get_admin_text("btn_back", language)),
        ]
    ]

    return ReplyKeyboardMarkup(
        keyboard=keyboard,
        resize_keyboard=True,
    )

