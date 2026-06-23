
from app.services.sync_roaming_service import MODEL_TYPES
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

SYNC_DOCUMENT_BUTTON_TEXT = "🔄 Синхронизация документа"
CANCEL_BUTTON_TEXT = "❌ Отмена"

def sync_start_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text=SYNC_DOCUMENT_BUTTON_TEXT)
            ],
        ],
        resize_keyboard=True,
    )

def sync_cancel_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text=CANCEL_BUTTON_TEXT),
            ],
        ],
        resize_keyboard=True,
    )

def sync_model_type_keyboard() -> ReplyKeyboardMarkup:
    rows = []

    for model_type, title in MODEL_TYPES.items():
        rows.append(
            [
                KeyboardButton(text=f"{title} = {model_type}")
            ]
        )

    rows.append(
        [
            KeyboardButton(text=CANCEL_BUTTON_TEXT),
        ]
    )

    return ReplyKeyboardMarkup(
        keyboard=rows,
        resize_keyboard=True,
    )

