# adapts an approved answer to the user's actual question using gemini
# removes irrelevant parts, fixes grammar, rephrases naturally
# called from priority_retriever.resolve_direct_answer when approved score >= direct threshold
# but the user question differs from the stored approved question

import logging
from google import genai
from app.config import GEMINI_API_KEY

log = logging.getLogger("bot.retriever")

client = genai.Client(api_key=GEMINI_API_KEY)

ADAPT_MODEL = "gemini-2.5-flash"

# maps language code to human-readable name for the prompt instruction
_LANGUAGE_NAMES = {
    "ru": "русском",
    "uz": "uzbek",
    "en": "English",
}

ADAPT_PROMPT = """Ты — ассистент поддержки Faktura.uz. Оператор уже дал проверенный ответ на похожий вопрос. Используй его как достоверный источник истины.

Проверенный вопрос: {approved_question}
Проверенный ответ оператора: {approved_answer}

Контекст из инструкций Faktura (если есть):
{pdf_context}

Текущий вопрос пользователя: {user_question}

Сформируй ответ на ТЕКУЩИЙ вопрос по правилам:
- Опирайся на проверенный ответ как на источник истины.
- Оставь только то, что относится к текущему вопросу; лишнее убери.
- Исправь грамматику и перефразируй естественно.
- НЕ выдумывай фактов: добавляй детали только если они есть в проверенном ответе или в контексте из инструкций.
- Сохрани все конкретные шаги, числа и названия без искажений.
- Отвечай кратко и по делу на {language} языке.

Ответ:"""


# adapts the approved answer to the user's actual question
# returns adapted text or falls back to the original approved answer on error
# called from priority_retriever.resolve_direct_answer
def adapt_answer(
    user_question: str,
    approved_question: str,
    approved_answer: str,
    pdf_context: str = "",
    language: str = "ru",
) -> str:

    if not approved_answer or not approved_answer.strip():
        return ""

    # map language code to readable name, fall back to code itself
    language_name = _LANGUAGE_NAMES.get(language, language)

    prompt = ADAPT_PROMPT.format(
        approved_question=(approved_question or "").strip(),
        approved_answer=approved_answer.strip(),
        pdf_context=(pdf_context or "нет").strip(),
        user_question=(user_question or "").strip(),
        language=language_name,
    )

    try:
        response = client.models.generate_content(
            model=ADAPT_MODEL,
            contents=prompt,
        )
        adapted = (response.text or "").strip()
        if adapted:
            log.info(f"  ✏️  adapt_answer: ответ адаптирован под вопрос пользователя")
            return adapted
        log.warning("  adapt_answer: Gemini вернул пустой ответ — используем оригинал из approved.csv")
        return approved_answer.strip()
    except Exception as err:
        log.warning(f"  adapt_answer: ошибка Gemini ({err}) — используем оригинал из approved.csv")
        return approved_answer.strip()
