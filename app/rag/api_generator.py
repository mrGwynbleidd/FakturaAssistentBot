from google import genai
from app.config import GEMINI_API_KEY
import time

from app.faktura_api.direct_formatter import format_api_answer_direct

client = genai.Client(api_key=GEMINI_API_KEY)

GEMINI_MODELS = [
    "gemini-2.5-flash",
    "gemini-2.5-flash-lite",
]


# БАГ 5 БЫЛ: весь код после direct_answer был вне функции из-за сломанных отступов
def generate_api_answer(
    question: str,
    api_context: str,
    language: str = "ru",
) -> str:

    # Сначала пробуем без Gemini
    direct_answer = format_api_answer_direct(
        question=question,
        api_context=api_context,
        language=language,
    )

    if direct_answer:
        return direct_answer

    # Если прямой форматтер не справился — идём в Gemini
    prompt = f"""
Ты - AI-помощник Faktura.uz.
Ты получаешь результаты реального Faktura API-запроса.
Твоя задача - объяснить пользователю результат API простым языком.

ФОРМАТИРОВАНИЕ (Telegram Markdown — строго соблюдать):
• Жирный:   *текст*       ← одна звёздочка с каждой стороны
• Курсив:   _текст_       ← нижнее подчёркивание
• Код:      `текст`       ← обратная кавычка
• ЗАПРЕЩЕНО использовать **двойные звёздочки** — они не рендерятся в Telegram
• ЗАПРЕЩЕНО использовать __двойное подчёркивание__


ВАЖНЫЕ ПРАВИЛА:
1. Не говори, что ты не можешь выполнить API-запрос. API-запрос уже выполнен.
2. Используй только данные из API_CONTEXT.
3. Не выдумывай данные.
4. Если API_CONTEXT содержит RAW_JSON_RESULT, объясни его пользователю.
5. Если результат true/false, объясни значение по INTERPRETATION_RULE.
6. Отвечай на языке пользователя.
7. Язык ответа: {language}.
8. Ответ должен быть кратким, понятным и практичным.

API_CONTEXT:
{api_context}

USER_QUESTION:
{question}
"""

    last_error = None

    for model in GEMINI_MODELS:
        for attempt in range(2):
            try:
                response = client.models.generate_content(
                    model=model,
                    contents=prompt,
                )
                return response.text.strip()

            except Exception as err:
                last_error = err
                import logging
                logging.getLogger("bot").warning(f"Gemini [{model}] attempt {attempt+1}: {err}")
                time.sleep(2)

    return build_api_fallback_answer(api_context, language, last_error)


def build_api_fallback_answer(
    api_context: str,
    language: str = "ru",
    error: Exception | None = None,
) -> str:
    if language == "en":
        return (
            "Faktura API returned data, but the AI model is temporarily unavailable.\n"
            f"Technical context:\n{api_context[:1500]}"
        )
    if language == "uz":
        return (
            "Faktura API ma'lumot qaytardi, lekin AI model vaqtincha mavjud emas.\n"
            f"Texnik kontekst:\n{api_context[:1500]}"
        )
    return (
        "Faktura API успешно вернул данные, но AI-модель временно недоступна.\n"
        f"Технический контекст:\n{api_context[:1500]}"
    )