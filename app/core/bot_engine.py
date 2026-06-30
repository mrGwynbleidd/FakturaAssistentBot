#orchestrates the full pipeline for a user question: incident check → RAG → API → Gemini → review save
#returns a result dict with answer, sources, review status
#used in bot/handlers.py for text questions and photo questions

import logging
log = logging.getLogger("bot.engine")

from app.bot.language import detect_language
from app.rag.retriever import retrieve_context
from app.rag.generator import generate_answer
from app.logs.csv_logger import save_qa
from app.learning.case_logger import save_case_for_review

from app.faktura_api.router import should_use_faktura_api, detect_api_intent
from app.faktura_api.api_answer import get_api_context
from app.rag.api_generator import generate_api_answer

from app.core.emergency_answer_checker import check_active_incidents

from app.core.answer_mode_logger import log_answer_mode

#minimum score distance above which a source is considered weak and sent to review
REVIEW_DISTANCE_THRESHOLD = 1.25


#returns true if any source in the list is flagged as critical, used to force review
def is_critical_case(sources: list[dict] | None) -> bool:
    if not sources:
        return False
    return any(s.get("is_critical") for s in sources if isinstance(s, dict))


#returns true if the top source has a distance above the threshold, indicating a poor match
#used in should_send_to_review
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


#returns true if the answer text contains phrases indicating the model couldn't find info
#used in should_send_to_review
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
        "yetarli ma'lumot topilmadi",
    ]
    answer_lower = answer.lower()
    return any(phrases in answer_lower for phrases in bad_phrases)


#decides whether to send the q/a pair to human review
#returns (should_review: bool, reason: str)
#used in process_user_question post-processing step
def should_send_to_review(answer: str, context: str, sources: list[dict]) -> tuple[bool, str]:
    if is_critical_case(sources):
        return True, "sync_mismatch_critical"
    if not context or not context.strip():
        return True, "empty_context"
    if not sources:
        return True, "no_sources"
    if has_weak_source(sources):
        return True, "weak_source_distance"
    if answer_looks_weak(answer):
        return True, "weak_answer_text"
    return False, "ok"


#main pipeline: runs incident check, RAG retrieval, optional faktura api call, gemini generation, and saves results
#returns a dict with answer, sources, sent_to_review, review_case_id, review_reason
#used in bot/handlers.py question_handler
def process_user_question(
        question: str,
        save_to_csv: bool = True,
        save_review_cases: bool = True,
        forced_language: str | None = None,
) -> dict:

    question = question.strip()

    #return early if question is empty
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
    log.info(f"")
    log.info(f"{'='*60}")
    log.info(f"❓ ВОПРОС [{language.upper()}]: {question[:100]}")
    log.info(f"{'='*60}")

    # ── 1. check active incidents ──────────────────────────────────────────────
    log.info(f"[1/5] Проверка активных инцидентов...")
    incident_result = check_active_incidents(question=question, language=language)

    #if a matching incident exists, return its answer directly without RAG or Gemini
    if incident_result:
        log.info(f"  🚨 ИНЦИДЕНТ совпал: {incident_result.get('incident_title','')!r}")
        log.info(f"  → Ответ из инцидента, без RAG и Gemini")
        try:
            log_answer_mode(
                mode="incident",
                question=question,
                answer=incident_result["answer"],
                source_type="incident",
                notes=incident_result.get("incident_title", ""),
            )
        except Exception:
            pass
        return {
            "answer": incident_result["answer"],
            "sources": incident_result["sources"],
            "sent_to_review": False,
            "review_case_id": None,
            "review_reason": None,
        }
    log.info(f"  ✓ Активных инцидентов не найдено")

    # ── 2. RAG search ──────────────────────────────────────────────────────────
    log.info(f"[2/5] RAG поиск (approved → admin_knowledge → pdf)...")

    from app.rag.priority_retriever import retrieve_priority_context

    context = ""
    sources = []
    is_api_request = False
    api_intent = None

    rag_result = retrieve_priority_context(question=question, language=language)
    rag_mode = rag_result.get("mode", "?")
    log.info(f"  RAG режим: {rag_mode}")

    # if rag_result.get("mode") == "direct_approved":
    #     answer = rag_result.get("answer", "")

    #     log_answer_mode(
    #         mode="direct_approved",
    #         source_type="approved",
    #         source_id=rag_result.get("source_id", "") or rag_result.get("case_id", ""),
    #         score=rag_result.get("score", ""),
    #         question=question,
    #         answer=answer,
    #         matched_question=rag_result.get("matched_question", ""),
    #         notes="approved answer used before Gemini/PDF",
    #     )

    #     return answer
    
    # if rag_result.get("mode") == "approved_candidate_not_direct":
    #     log_answer_mode(
    #         mode="approved_candidate_not_direct",
    #         source_type="approved",
    #         source_id=rag_result.get("source_id", "") or rag_result.get("case_id", ""),
    #         score=rag_result.get("score", ""),
    #         question=question,
    #         answer=rag_result.get("answer", "") or rag_result.get("candidate_answer", ""),
    #         matched_question=rag_result.get("matched_question", ""),
    #         notes="approved candidate found but score is below direct threshold",
    #     )

    #if a direct high-confidence match is found, return without calling Gemini
    if rag_mode in {"direct_approved", "direct_admin_knowledge"}:
        answer = rag_result.get("answer", "")
        src = rag_result.get("sources", [])
        log.info(f"  ✅ ПРЯМОЙ ОТВЕТ из базы знаний — Gemini не нужен")
        log.info(f"  → Длина ответа: {len(answer)} символов")
        try:
            top = src[0] if src else {}
            log_answer_mode(
                mode=rag_mode,
                question=question,
                answer=answer,
                source_type=top.get("source_type", ""),
                source_id=str(top.get("source_id", "") or top.get("id", "")),
                score=top.get("score", ""),
                matched_question=str(top.get("question", "") or top.get("matched_question", "")),
            )
        except Exception:
            pass
        return {
            "answer": answer,
            "sources": src,
            "sent_to_review": False,
            "review_case_id": None,
            "review_reason": None,
        }

    context = rag_result.get("context_text", "")
    sources = rag_result.get("sources", [])
    log.info(f"  Контекст для LLM: {len(context)} символов, источников: {len(sources)}")

    # ── 3. Faktura API ─────────────────────────────────────────────────────────
    log.info(f"[3/5] Проверка необходимости Faktura API...")
    try:
        if should_use_faktura_api(question):
            api_intent = detect_api_intent(question)
            if api_intent:
                is_api_request = True
                log.info(f"  🔌 API-запрос: intent={api_intent}")
                #replace rag context with live api data
                context, sources = get_api_context(question, api_intent)
                log.info(f"  API контекст: {len(context)} символов, источников: {len(sources)}")
            else:
                log.info(f"  API intent не определён — используем RAG контекст")
        else:
            log.info(f"  ✓ API не нужен для этого вопроса")

    except Exception as error:
        log.error(f"  ❌ Ошибка retriever/API: {error}", exc_info=True)
        error_answer = f"Error in searching context in base of knowledge: {error}"
        review_case_id = None
        if save_review_cases:
            review_case_id = save_case_for_review(
                question=question, bot_answer=error_answer, language=language,
                sources=[], reason="retriever_or_api_error", notes=str(error),
            )
        if save_to_csv:
            save_qa(question=question, answer=error_answer, language=language, sources=[])
        return {
            "success": False, "language": language, "question": question,
            "answer": error_answer, "sources": [], "context": "",
            "sent_to_review": True, "review_case_id": review_case_id,
            "review_reason": "retriever_or_api_error",
        }

    # ── 4. generate answer with Gemini ─────────────────────────────────────────
    log.info(f"[4/5] Генерация ответа (Gemini) | api_request={is_api_request}...")
    try:
        if is_api_request:
            answer = generate_api_answer(question=question, api_context=context, language=language)
        else:
            answer = generate_answer(question=question, context=context, language=language)
        log.info(f"  ✓ Gemini ответил, длина: {len(answer)} символов")

    except Exception as error:
        log.error(f"  ❌ Ошибка генерации: {error}", exc_info=True)
        error_answer = f"Error in generating answer: {error}"
        review_case_id = None
        if save_review_cases:
            review_case_id = save_case_for_review(
                question=question, bot_answer=error_answer, language=language,
                sources=sources, reason="generator_error", notes=str(error),
            )
        if save_to_csv:
            save_qa(question=question, answer=error_answer, language=language, sources=sources)
        
        # log_answer_mode(
        #     mode="pdf_rag_or_llm",
        #     source_type="pdf_or_llm",
        #     question=question,
        #     answer=answer,
        #     notes="approved direct answer was not used"
        # )
        
        return {

            "success": False, "language": language, "question": question,
            "answer": error_answer, "sources": sources, "context": context,
            "sent_to_review": True, "review_case_id": review_case_id,
            "review_reason": "generator_error",
        }

    # ── 5. save and optionally flag for review ─────────────────────────────────
    log.info(f"[5/5] Пост-обработка...")

    if save_to_csv:
        try:
            save_qa(question=question, answer=answer, language=language, sources=sources)
            log.info(f"  ✓ Сохранено в QA_outputs.csv")
        except Exception as error:
            log.warning(f"  ⚠️  CSV save error: {error}")

    sent_to_review = False
    review_case_id = None
    review_reason = None

    need_review, reason = should_send_to_review(answer=answer, context=context, sources=sources)
    log.info(f"  Нужна проверка: {need_review} | причина: {reason}")

    if save_review_cases and need_review:
        try:
            review_case_id = save_case_for_review(
                question=question, bot_answer=answer, language=language,
                sources=sources, reason=reason,
                notes="Auto-saved by bot_engine because answer/context/source quality is weak.",
            )
            sent_to_review = True
            review_reason = reason
            log.info(f"  📝 Сохранён на проверку ({reason}) → {review_case_id}")
        except Exception as error:
            log.warning(f"  ⚠️  Review case save error: {error}")

    log.info(f"✅ ОТВЕТ ОТПРАВЛЕН | на_проверке={sent_to_review} | причина={review_reason or 'ok'}")

    try:
        top = sources[0] if sources else {}
        log_answer_mode(
            mode="api" if is_api_request else "llm_context",
            question=question,
            answer=answer,
            source_type=top.get("source_type", ""),
            source_id=str(top.get("source_id", "") or top.get("id", "")),
            score=top.get("score", ""),
            notes=f"sent_to_review={sent_to_review} reason={review_reason or 'ok'}",
        )
    except Exception:
        pass

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


from app.rag.image_analyzer import analyze_sceenshot


#handles image input: extracts text from screenshot via gemini, then runs process_user_question
#returns same result dict as process_user_question with added image_description field
#used in bot/handlers.py photo_handler
def process_user_image(
        image_bytes: bytes,
        caption: str = "",
        save_to_csv: bool = True,
        save_review_cases: bool = True,
        forced_language: str | None = None,
) -> dict:

    language = forced_language or "ru"
    log.info(f"🖼  Обработка изображения | caption={repr(caption[:50])}")

    try:
        image_info = analyze_sceenshot(image_bytes, language=language)
    except Exception as err:
        log.error(f"  ❌ Ошибка анализа изображения: {err}")
        return {
            "success": False, "language": language,
            "question": caption or "[изображение]",
            "answer": f"Не удалось проанализировать изображение: {err}",
            "sources": [], "context": "",
            "sent_to_review": False, "review_case_id": None,
            "review_reason": None, "image_description": "",
        }

    extracted_text = image_info.get("extracted_text", "")
    search_query = image_info.get("search_query", "")
    description = image_info.get("description", "")
    gemini_error = image_info.get("error")

    log.info(f"  extracted_text: {repr(extracted_text[:60])}")
    log.info(f"  search_query:   {repr(search_query[:60])}")
    log.info(f"  description:    {repr(description[:60])}")

    #prefer search_query, fall back to extracted_text, then description
    effective_query = search_query or extracted_text or description

    #if no usable text was extracted, save to review and return a fallback message
    if not effective_query:
        if gemini_error:
            log.warning(f"  Gemini image error: {gemini_error}")
        no_text_answer = {
            "ru": "Не смог распознать содержимое изображения. Опишите проблему текстом.",
            "uz": "Rasmdan matnni tanib bo'lmadi. Muammoni matn orqali tasvirlang.",
            "en": "Could not extract content from the image. Please describe the issue in text.",
        }
        review_case_id = None
        if save_review_cases:
            try:
                review_case_id = save_case_for_review(
                    question=caption or "[изображение без текста]",
                    bot_answer=no_text_answer.get(language, no_text_answer["ru"]),
                    language=language, sources=[],
                    reason="image_unrecognized",
                    notes="Gemini не смог извлечь текст или описание из фото.",
                )
                log.info(f"  📝 Нераспознанное фото → review ({review_case_id})")
            except Exception as err:
                log.warning(f"  Could not save image review case: {err}")
        return {
            "success": False, "language": language,
            "question": caption or "[изображение]",
            "answer": no_text_answer.get(language, no_text_answer["ru"]),
            "sources": [], "context": "",
            "sent_to_review": review_case_id is not None,
            "review_case_id": review_case_id,
            "review_reason": "image_unrecognized", "image_description": "",
        }

    #combine caption and extracted text for the rag query
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

    #prepend screenshot description to the final answer
    if description:
        prefix = {
            "ru": f"🖼 *На скриншоте:* {description}\n\n",
            "uz": f"🖼 *Skrinshot:* {description}\n\n",
            "en": f"🖼 *Screenshot:* {description}\n\n",
        }.get(language, f"🖼 {description}\n\n")
        rag_result["answer"] = prefix + rag_result["answer"]

    rag_result["image_description"] = description
    return rag_result
