from google import genai
from app.config import GEMINI_API_KEY
import time

client = genai.Client(api_key=GEMINI_API_KEY)

GEMINI_MODELS = [
    "gemini-2.5-flash",
    "gemini-2.5-flash-lite",
]


def generate_answer(question: str, context: str, language: str = "ru") -> str:

    # БАГ БЫЛ ЗДЕСЬ: context мог прийти как bool (True/False от Faktura API)
    # Принудительно приводим к строке
    if not isinstance(context, str):
        context = str(context)

    if not context or not context.strip():
        return get_no_context_answer(language)

    prompt = f"""
Ты — AI-помощник службы поддержки Faktura.uz.

Твоя задача — помогать пользователям по инструкциям из базы знаний.
Во время написания текста помни что ответ напишется в Telegrem, поэтом ты должен выделять жирным, курсивов, цитата и тд как следует для Telegram, чтобы в нем твой ответ отображался без лишних артефактов как *

ВАЖНЫЕ ПРАВИЛА:
1. Отвечай только на основе CONTEXT.
2. Если в CONTEXT нет точной инструкции, НЕ говори просто "информации нет".
3. Если вопрос связан со входом, аккаунтом, паролем, ЭЦП, кодом подтверждения или сотрудником:
   - используй найденную информацию о регистрации, пароле, ЭЦП, подтверждении и сотрудниках;
   - дай безопасные шаги проверки;
   - если отдельной инструкции по сбросу пароля нет, скажи это честно.
4. Не называй кнопки, разделы или функции, которых нет в CONTEXT.
5. Отвечай на языке пользователя.
6. Язык ответа: {language}.
7. Ответ должен быть практичным, спокойным и понятным.
8. Не используй знания вне CONTEXT.

ФОРМАТ ОТВЕТА:
- Краткий ответ
- Что можно проверить
- Если в базе нет точной инструкции — честно напиши это
- Источник / основание из базы, если возможно

CONTEXT:
{context}

QUESTION:
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

    return get_model_unavaiable_answer(language, last_error)


def get_no_context_answer(language: str = "ru") -> str:
    if language == "en":
        return (
            "I could not find enough info in knowledge base to answer this question.\n"
            "Please contact Faktura.uz or call our call center 📞 **+998 71 200 00 13**"
        )
    if language == "uz":
        return (
            "Men bu savolga javob berish uchun bilim bazasida yetarli ma'lumot topa olmadim.\n"
            "Iltimos, Faktura.uz bilan bog'laning yoki bizning qo'ng'iroqlar markazimizga "
            "qo'ng'iroq qiling 📞 **+998 71 200 00 13**"
        )
    return (
        "В базе знаний я не нашел достаточно информации, чтобы ответить на этот вопрос.\n"
        "Пожалуйста, свяжитесь с Faktura.uz или позвоните в наш колл-центр 📞 **+998 71 200 00 13**"
    )


def get_model_unavaiable_answer(language: str = "ru", error: Exception | None = None) -> str:
    if language == "en":
        return (
            "The AI model is temporarily unavailable due to high demand. "
            "Please try again later."
        )
    if language == "uz":
        return (
            "AI model hozircha yuqori yuklama sababli vaqtincha mavjud emas. "
            "Iltimos, birozdan keyin qayta urinib ko'ring."
        )
    return (
        "AI-модель временно недоступна из-за высокой нагрузки. "
        "Пожалуйста, попробуйте повторить запрос позже."
    )