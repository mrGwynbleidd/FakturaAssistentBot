#read API key from .env

import os
from dotenv import load_dotenv

load_dotenv()

#load API key
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

FAKTURA_USERNAME = os.getenv("FAKTURA_USERNAME")
FAKTURA_PASSWORD = os.getenv("FAKTURA_PASSWORD")
FAKTURA_CLIENT_ID = os.getenv("FAKTURA_CLIENT_ID")
FAKTURA_CLIENT_SECRET = os.getenv("FAKTURA_CLIENT_SECRET")

FAKTURA_API_BASE_URL = os.getenv("FAKTURA_API_BASE_URL", "https://api.faktura.uz")
FAKTURA_ACCOUNT_URL = os.getenv("FAKTURA_ACCOUNT_URL", "https://account.faktura.uz")

ADMIN_IDS: set[int] = {int(x) for x in os.getenv("ADMIN_IDS", "").split(",") if x.strip()}


#if not found API key
if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY not founded in .env")

if not TELEGRAM_BOT_TOKEN:
    raise ValueError("TELEGRAM_BOT_TOKEN not founded in .env")