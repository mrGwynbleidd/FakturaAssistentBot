from app.admin.texts.ru import ADMIN_TEXTS_RU
from app.admin.texts.en import ADMIN_TEXTS_EN
from app.admin.texts.uz import ADMIN_TEXTS_UZ

ADMIN_TEXTS = {
        "ru": ADMIN_TEXTS_RU,
        "uz": ADMIN_TEXTS_UZ,
        "en": ADMIN_TEXTS_EN
    }

def get_admin_text(key: str, language: str = "ru") -> str:
    
    language_texts = ADMIN_TEXTS.get(language, ADMIN_TEXTS_RU)

    return language_texts.get(key, ADMIN_TEXTS_RU.get(key, key),)

__all__ = [
    "ADMIN_TEXTS",
    "ADMIN_TEXTS_RU",
    "ADMIN_TEXTS_UZ",
    "ADMIN_TEXTS_EN",
    "get_admin_text",
]