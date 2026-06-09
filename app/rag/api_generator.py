from google import genai
from app.config import GEMINI_API_KEY
import time

from app.faktura_api.direct_formatter import format_api_answer_direct


client = genai.Client(api_key=GEMINI_API_KEY)

GEMINI_MODELS = [
    "gemini-2.5-flash",
    "gemini-2.0-flash",
]

def generate_api_answer(
        question: str,
        api_context: str,
        language: str = "ru",
) -> str:
    
    direct_answer = format_api_answer_direct(
        question=question,
        api_context=api_context,
        language=language,
    )
    

    if direct_answer:
        return direct_answer
    
    
    prompt = f"""
Ты - AI-помощник Faktura.uz.
Ты получаешь результаты реального Faktura API-запросы.
Твоя-задача - объяснить пользователю результат API простым языком.

ВАЖНЫЕ ПРАВИЛА:
1. Не говори, что ты не можешь выполнить API-запрос. API-запрос уже выполнен.
2. Использую только данные из API_CONTEXT.
3. Не выдумавай данные.
4. Если API_CONTEXT содержит RAW_JSON_RESULT, объясни его пользователю
5. Если результат true/false, объясни значения по INTERPRETATION_RULE.
6. Отвечай на языке пользователя.
7. Язык ответаЖ {language}.
8. Ответ должен быть кротким, понятным и проктичным.

API_Context:
{api_context},

USER_QUESTION:
{question},

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
                print(f"Gemini API Error. Model={model}. attempt={attempt +1}, error = {err}")
                time.sleep(2)

    return build_api_fallback_answer(api_context, language, last_error)

    



def build_api_fallback_answer(
        api_context: str,
        language: str = "ru",
        error: Exception | None = None,
) -> str:
    if language == "en":
        return (
            "Faktura API returned data, but the AI model is temporarily unavailable. "
            "Please try again later.\n\n"
            f"Technical context:\n{api_context[:1500]}"
        )

    if language == "uz":
        return (
            "Faktura API ma’lumot qaytardi, lekin AI model vaqtincha mavjud emas. "
            "Iltimos, birozdan keyin qayta urinib ko‘ring.\n\n"
            f"Texnik kontekst:\n{api_context[:1500]}"
        )

    return (
        "Faktura API успешно вернул данные, но AI-модель временно недоступна. "
        "Попробуйте повторить запрос позже.\n\n"
        f"Технический контекст:\n{api_context[:1500]}"
    )
    






