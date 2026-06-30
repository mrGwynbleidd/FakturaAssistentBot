from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from app.admin.texts import get_admin_text


# keyboard shown while browsing cases one by one
# buttons: approve, reject (row 1) / skip, back (row 2)
def review_case_keyboard(language: str = "ru") -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text=get_admin_text("btn_confirm", language)),
                KeyboardButton(text=get_admin_text("btn_reject", language)),
            ],
            [
                KeyboardButton(text=get_admin_text("btn_skip", language)),
                KeyboardButton(text=get_admin_text("btn_back", language)),
            ],
        ],
        resize_keyboard=True,
    )


# keyboard shown after all cases are reviewed or after leaving review
def review_after_action_keyboard(language: str = "ru") -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text=get_admin_text("btn_review_cases", language)),
                KeyboardButton(text=get_admin_text("btn_back", language)),
            ],
        ],
        resize_keyboard=True,
    )
