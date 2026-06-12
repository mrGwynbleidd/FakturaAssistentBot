# Analyze photo through Gemini vision.
# Two-stage approach:
#   Stage 1 — structured JSON prompt (extracts text + search query)
#   Stage 2 — plain description fallback if Stage 1 yields nothing

import json
import logging
import time

from google import genai
from google.genai import types
from app.config import GEMINI_API_KEY

log = logging.getLogger("bot")
client = genai.Client(api_key=GEMINI_API_KEY)

GEMINI_MODELS = [
    "gemini-2.5-flash",
    "gemini-2.0-flash",
]


def _detect_mime_type(image_bytes: bytes) -> str:
    """Detect image format from magic bytes."""
    if image_bytes[:8] == b"\x89PNG\r\n\x1a\n":
        return "image/png"
    if image_bytes[:4] == b"GIF8":
        return "image/gif"
    if image_bytes[:4] == b"RIFF" and image_bytes[8:12] == b"WEBP":
        return "image/webp"
    return "image/jpeg"  # default


def _call_gemini(image_bytes: bytes, prompt: str, mime_type: str) -> str | None:
    """Try every model × 2 attempts. Returns raw text or None."""
    last_err = None
    for model in GEMINI_MODELS:
        for attempt in range(2):
            try:
                response = client.models.generate_content(
                    model=model,
                    contents=[
                        types.Part.from_bytes(data=image_bytes, mime_type=mime_type),
                        prompt,
                    ],
                )
                return response.text.strip()
            except Exception as err:
                last_err = err
                log.warning(f"Gemini vision [{model}] attempt {attempt + 1}: {err}")
                time.sleep(2)
    log.warning(f"All Gemini models failed: {last_err}")
    return None


# ── Stage 1 prompt ──
_STAGE1_PROMPT = """
Ты — AI-ассистент службы поддержки Faktura.uz.
Пользователь прислал скриншот. Проанализируй изображение.

ЗАДАЧА:
1. Найди и выпиши дословно любой текст ошибки, сообщения или уведомления.
   Если текста нет — оставь поле пустым.
2. Опиши одним предложением что видно: раздел/экран/форма системы Faktura.uz.
3. ОБЯЗАТЕЛЬНО сформулируй поисковый запрос для базы знаний Faktura.uz.
   Даже если текста нет — составь запрос по тому, что видно на экране.

ФОРМАТ ОТВЕТА (строго JSON, без markdown-обёртки):
{
    "extracted_text": "дословный текст с экрана, или пустая строка",
    "search_query": "запрос для поиска в базе знаний (ВСЕГДА заполнять)",
    "description": "одно предложение — что видно на скриншоте"
}
"""

# ── Stage 2 prompt (plain text, no JSON) ──
_STAGE2_PROMPT = """
Посмотри на это изображение и ответь на русском языке:
1. Что изображено? (интерфейс, форма, ошибка, таблица и т.д.)
2. Если есть текст — перепиши его дословно.
3. Какой вопрос пользователь скорее всего хочет задать?

Отвечай коротко, в свободной форме.
"""


def analyze_sceenshot(image_bytes: bytes, language: str = "ru") -> dict:
    mime_type = _detect_mime_type(image_bytes)

    # ── Stage 1: structured JSON ──
    raw = _call_gemini(image_bytes, _STAGE1_PROMPT, mime_type)
    if raw:
        try:
            clean = raw.removeprefix("```json").removeprefix("```").removesuffix("```").strip()
            result = json.load(clean)
            # data = json.loads(clean)
            # with open("data.json", 'r') as file:
            #     result = json.load(file)

            # extracted1 = result['extraced_text']
            # search_query1= result['search_query']
            # description1 = result['description']

            
            #get - any function!
            extracted = result.get("extracted_text", "").strip()
            search_query = result.get("search_query", "").strip()
            description = result.get("description", "").strip()

            if search_query or extracted or description:
                log.info(f"📷 Фото распознано (Stage 1): {description[:60]}")
                return {
                    "extracted_text": extracted,
                    "search_query": search_query,
                    "description": description,
                }
        except (json.JSONDecodeError, ValueError):
            # JSON broken — fall through to Stage 2
            pass

    # ── Stage 2: plain description fallback ──────────────────────────────────
    log.info("📷 Stage 1 не дал результата, пробуем Stage 2...")
    raw2 = _call_gemini(image_bytes, _STAGE2_PROMPT, mime_type)
    if raw2 and raw2.strip():
        log.info(f"📷 Фото распознано (Stage 2): {raw2[:60]}")
        return {
            "extracted_text": "",
            "search_query": raw2.strip(),   # use the whole description as query
            "description": raw2.strip()[:200],
        }

    # ── Both stages failed ────────────────────────────────────────────────────
    return {
        "extracted_text": "",
        "search_query": "",
        "description": "",
        "error": "All Gemini models failed for both stages",
    }
