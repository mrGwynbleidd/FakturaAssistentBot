#analyze photo through Gemini

import base64
from google import genai
from google.genai import types
from app.config import GEMINI_API_KEY
import time

client = genai.Client(api_key=GEMINI_API_KEY)

GEMINI_MODELS = [
    "gemini-2.5-flash",
    "gemini-2.0-flash",
]

def analyze_sceenshot(image_bytes: bytes, language: str = "ru") -> dict:

    prompt = f"""
Ты - AI-ассистент службы поддержки Faktura.uz.
Пользователь прислал скриншот. Проанализируй изображение.

ЗАДАЧА:
1. Найди и выпиши дословно любой текст ошибки, сообщения или уведомления на скриншоте.
2. Если видишь форму, таблицу или интерфейс - опиши кратко чтотам происходит.
3. Сформулируй поисковый запрос (1-2 предложения) для поиска в базе знаний Faktura.uz.

ЯЗЫК ОТВЕТА: {language}

фОРМАТ ОТВЕТА (строго JSON)
{{
    "extracted_text": "дословный текст с экрана или описание проблемы",
    "search_query": "краткий запрос для поиска в базе знаний",
    "description": "одно предложение - что видно на скринщоте"
}}

Отвечай ТОЛЬКО валидным JSON без markdown-обёртки.
"""
    
    last_error = None

    for model in GEMINI_MODELS:
        for attempt in range(2):
            try:
                response = client.models.generate_content(
                    model=model,
                    contents=[
                        types.Part.from_bytes(
                            data=image_bytes,
                            mime_type="image/jpeg",
                        ),
                        prompt,
                    ],
                )

                import json
                raw = response.text.strip()
                # убираем ```json если вдруг Gemini добавил
                raw = raw.removeprefix("```json").removeprefix("```").removesuffix("```").strip()
                result = json.loads(raw)

                return {
                    #######
                    "extracted_text": result.get("extracted_text", ""),
                    "search_query": result.get("search_query", ""),
                    "description": result.get("description", ""),
                }
            except Exception as err:
                last_error = err
                print(f"[image_analyzer] model={model}, attempt = {attempt +1},error ={err}")
                time.sleep(2)

    return {
        "extraced_text": "",
        "search_query": "",
        "description":  "",
        "error": str(last_error),
    }