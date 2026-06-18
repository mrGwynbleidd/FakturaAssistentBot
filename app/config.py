import os
from pathlib import Path
from dotenv import load_dotenv

# Явно указываем путь к .env — всегда найдёт независимо откуда запускаешь
load_dotenv(Path(__file__).resolve().parents[1] / ".env")

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

FAKTURA_USERNAME = os.getenv("FAKTURA_USERNAME")
FAKTURA_PASSWORD = os.getenv("FAKTURA_PASSWORD")
FAKTURA_CLIENT_ID = os.getenv("FAKTURA_CLIENT_ID")
FAKTURA_CLIENT_SECRET = os.getenv("FAKTURA_CLIENT_SECRET")

FAKTURA_API_BASE_URL = os.getenv("FAKTURA_API_BASE_URL", "https://api.faktura.uz")
FAKTURA_ACCOUNT_URL = os.getenv("FAKTURA_ACCOUNT_URL", "https://account.faktura.uz")

HF_TOKEN = os.getenv("HF_TOKEN")

EMAIL= os.getenv("EMAIL")
API_PARAM= os.getenv("API_PARAM")

CALL_CENTER_DOMAIN = os.getenv("CALL_CENTER_DOMAIN")

ADMIN_IDS=os.getenv("ADMIN_IDS", "")


if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY not found in .env")

if not TELEGRAM_BOT_TOKEN:
    raise ValueError("TELEGRAM_BOT_TOKEN not found in .env")


COLLECT_GROUP_PHOTOS_ONLY = (
    os.getenv("COLLECT_GROUP_PHOTOS_ONLY", "False").lower() == "true"
)

GROUP_PHOTO_SAVE_DIR = os.getenv("GROUP_PHOTOS_SAVE_DIR", "data/group_photos",)

