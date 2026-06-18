#Main file will manage with whole process

import logging
log = logging.getLogger("bot")

#import all nessecary libs
from app.bot.language import detect_language
from app.rag.retriever import retrieve_context
from app.rag.generator import generate_answer
from app.logs.csv_logger import save_qa
from app.learning.case_logger import save_case_for_review

from app.faktura_api.router import should_use_faktura_api, detect_api_intent
from app.faktura_api.api_answer import get_api_context
from app.rag.api_generator import generate_api_answer

from app.core.emergency_answer_checker import check_active_incidents

REVIEW_DISTANCE_THRESHOLD = 1.25

# check if any source is flagged as CRITICAL (e.g., sync mismatch)
def is_critical_case(sources: list[dict] | None) -> bool:
    if not sources:
        return False
    return any(s.get("is_critical") for s in sources if isinstance(s, dict))


#check if is it weak or no context
#less distance - better
#top distance too high -> founded context irrelevant
def has_weak_source(source: list[dict] | None) -> bool:
    
    if not source:
        return True
    
    first_source = source[0]
    distance = first_source.get("distance")

    if distance is None:
        return False
    
    try:
        return float(distance) > REVIEW_DISTANCE_THRESHOLD
    except (TypeError, ValueError):
        return False
    

# check is answer bad or not full
def answer_looks_weak(answer: str) -> bool:

    if not answer or not answer.strip():
        return True
    
    bad_phrases = [
        "нет достаточной информации",
        "информации недостаточно",
        "не удалось найти",
        "не могу найти",
        "не найдено",
        "not enough information",
        "could not find enough information",
        "i could not find",
        "yetarli ma’lumot topilmadi",
        "yetarli ma'lumot topilmadi",
    ]

    answer_lower = answer.lower()

    return any(phrases in answer_lower for phrases in bad_phrases)



#choose should it send these case for review
#return t/f and reason
def should_send_to_review(answer: str, context: str, sources: list[dict]) -> tuple[bool, str]:
    # CRITICAL flag always forces review (e.g. sync mismatch between Faktura and Soliq)
    if is_critical_case(sources):
        return True, "sync_mismatch_critical"

    #if no context
    if not context or not context.strip():
        return True, "empty_context"

    if not sources:
        return True, "no_sources"

    if has_weak_source(sources):
        return True, "weak_source_distance"

    if answer_looks_weak(answer):
        return True, "weak_answer_text"

    return False, "ok"
    

# Get question from user, return answer
# check question -> detect language -> 
# search context in Chroma -> Give question and context to Gemini -> 
# save q/a in csv -> return result
def process_user_question(question: str, save_to_csv: bool = True, save_review_cases: bool = True, forced_language: str | None = None,) -> dict:
    
    question = question.strip()

    if not question:
        return {
            "success": False,
            "language": "unknown",
            "question": question,
            "answer": "Пожалуйста, напишите вопрос",
            "sources": [],
            "context": "",
            "sent_to_review": False,
            "review_case_id": None,
            "review_reason": None,
        }

    language = forced_language or detect_language(question)

    incident_result = check_active_incidents(
        question=question,
        language=language,
    )

    if incident_result:
        return {
            "answer": incident_result["answer"],
            "sources": incident_result["sources"],
            "sent_to_review": False,
            "review_case_id": None,
            "review_reason": None,
        }

    log.info(f"❓ Вопрос [{language.upper()}]: {question[:80]}")

    context = ""
    sources = []
    is_api_request = False
    api_intent = None

    try:
        if should_use_faktura_api(question):
            api_intent = detect_api_intent(question)
            if api_intent:
                is_api_request = True
                log.info(f"🔌 API-запрос: {api_intent}")
                context, sources = get_api_context(question, api_intent)
            else:
                log.info("📚 Поиск в базе знаний...")
                context, sources = retrieve_context(question, n_results=5)
        else:
            log.info("📚 Поиск в базе знаний...")
            context, sources = retrieve_context(question, n_results=5)

    except Exception as error:
        error_answer = f"Error in searching context in base of knowledge: {error}"

        review_case_id = None

        if save_review_cases:
            review_case_id = save_case_for_review(
                question=question,
                bot_answer=error_answer,
                language=language,
                sources=[],
                reason="retriever_or_api_error",
                notes=str(error),
            )

        if save_to_csv:
            save_qa(
                question=question,
                answer=error_answer,
                language=language,
                sources=[],
            )

        return {
            "success": False,
            "language": language,
            "question": question,
            "answer": error_answer,
            "sources": [],
            "context": "",
            "sent_to_review": True,
            "review_case_id": review_case_id,
            "review_reason": "retriever_or_api_error",
        }

    try:
        log.info("🤖 Генерация ответа (Gemini)...")
        if is_api_request:
            answer = generate_api_answer(
                question=question,
                api_context=context,
                language=language,
            )
        else:
            answer = generate_answer(
                question=question,
                context=context,
                language=language,
            )

    except Exception as error:
        error_answer = f"Error in generating answer: {error}"

        review_case_id = None

        if save_review_cases:
            review_case_id = save_case_for_review(
                question=question,
                bot_answer=error_answer,
                language=language,
                sources=sources,
                reason="generator_error",
                notes=str(error),
            )

        if save_to_csv:
            save_qa(
                question=question,
                answer=error_answer,
                language=language,
                sources=sources,
            )

        return {
            "success": False,
            "language": language,
            "question": question,
            "answer": error_answer,
            "sources": sources,
            "context": context,
            "sent_to_review": True,
            "review_case_id": review_case_id,
            "review_reason": "generator_error",
        }

    if save_to_csv:
        try:
            save_qa(question=question, answer=answer, language=language, sources=sources)
        except Exception as error:
            log.warning(f"CSV save error: {error}")

    sent_to_review = False
    review_case_id = None
    review_reason = None

    need_review, reason = should_send_to_review(answer=answer, context=context, sources=sources)

    if save_review_cases and need_review:
        try:
            review_case_id = save_case_for_review(
                question=question,
                bot_answer=answer,
                language=language,
                sources=sources,
                reason=reason,
                notes="Auto-saved by bot_engine because answer/context/source quality is weak.",
            )
            sent_to_review = True
            review_reason = reason
            log.info(f"📝 Сохранён на проверку ({reason})")
        except Exception as error:
            log.warning(f"Review case save error: {error}")

    log.info("✅ Ответ отправлен")

    return {
        "success": True,
        "language": language,
        "question": question,
        "answer": answer,
        "sources": sources,
        "context": context,
        "sent_to_review": sent_to_review,
        "review_case_id": review_case_id,
        "review_reason": review_reason,
    }

#take user screenshots
#Gemini vision extracts text from photo
#result goes to base RAG pipeline

from app.rag.image_analyzer import analyze_sceenshot

def process_user_image(
        image_bytes: bytes,
        caption: str = "",
        save_to_csv: bool = True,
        save_review_cases: bool = True,
        forced_language: str | None = None,
) -> dict:

    language = forced_language or "ru"

    # analyze photo with Gemini vision
    try:
        image_info = analyze_sceenshot(image_bytes, language=language)
    except Exception as err:
        return {
            "success": False,
            "language": language,
            "question": caption or "[изображение]",
            "answer": f"Не удалось проанализировать изображение: {err}",
            "sources": [], "context": "",
            "sent_to_review": False,
            "review_case_id": None,
            "review_reason": None,
            "image_description": "",
        }

    extracted_text = image_info.get("extracted_text", "")
    search_query = image_info.get("search_query", "")
    description = image_info.get("description", "")
    gemini_error = image_info.get("error")

    # use description as fallback search query when Gemini couldn't extract text
    # (e.g. all models failed, or image has no readable text but was described)
    effective_query = search_query or extracted_text or description

    if not effective_query:
        if gemini_error:
            log.warning(f"Gemini image error: {gemini_error}")
        no_text_answer = {
            "ru": "Не смог распознать содержимое изображения. Опишите проблему текстом.",
            "uz": "Rasmdan matnni tanib bo'lmadi. Muammoni matn orqali tasvirlang.",
            "en": "Could not extract content from the image. Please describe the issue in text.",
        }
        # Save to review so admin can manually describe it →
        # that description gets indexed and helps with similar future images
        review_case_id = None
        if save_review_cases:
            try:
                review_case_id = save_case_for_review(
                    question=caption or "[изображение без текста]",
                    bot_answer=no_text_answer.get(language, no_text_answer["ru"]),
                    language=language,
                    sources=[],
                    reason="image_unrecognized",
                    notes="Gemini не смог извлечь текст или описание из фото. "
                          "Опишите вручную что на изображении и дайте правильный ответ.",
                )
                log.info(f"📝 Нераспознанное фото сохранено на проверку ({review_case_id})")
            except Exception as err:
                log.warning(f"Could not save image review case: {err}")

        return {
            "success": False,
            "language": language,
            "question": caption or "[изображение]",
            "answer": no_text_answer.get(language, no_text_answer["ru"]),
            "sources": [], "context": "",
            "sent_to_review": review_case_id is not None,
            "review_case_id": review_case_id,
            "review_reason": "image_unrecognized",
            "image_description": "",
        }

    # build the question for the RAG pipeline
    if caption:
        combined_question = f"{caption}\n\n[Текст со скриншота]: {extracted_text}" if extracted_text else caption
    else:
        combined_question = extracted_text or description

    rag_result = process_user_question(
        question=search_query or combined_question,
        save_to_csv=save_to_csv,
        save_review_cases=save_review_cases,
        forced_language=language,
    )

    # prepend screenshot description to the answer
    if description:
        prefix = {
            "ru": f"🖼 *На скриншоте:* {description}\n\n",
            "uz": f"🖼 *Skrinshot:* {description}\n\n",
            "en": f"🖼 *Screenshot:* {description}\n\n",
        }.get(language, f"🖼 {description}\n\n")
        rag_result["answer"] = prefix + rag_result["answer"]

    rag_result["image_description"] = description
    return rag_result


