#Main file will manage with whole process

#import all nessecary libs
from app.bot.language import detect_language
from app.rag.retriever import retrieve_context
from app.rag.generator import generate_answer
from app.logs.csv_logger import save_qa
from app.learning.case_logger import save_case_for_review

from app.faktura_api.router import should_use_faktura_api, detect_api_intent
from app.faktura_api.api_answer import get_api_context
from app.rag.api_generator import generate_api_answer

REVIEW_DISTANCE_THRESHOLD = 1.25

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
    
    #Check question

    question = question.strip()
    

    #if question is empty
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
    
    #Detect language
    language = forced_language or detect_language(question)

    context = ""
    sources = []
    is_api_request = False
    api_intent = None

    #Search context in Chroma
    try:
        if should_use_faktura_api(question):
            api_intent = detect_api_intent(question)

            if api_intent:
                is_api_request = True
                context, sources = get_api_context(question, api_intent)

                print("IS API REQUEST:", is_api_request)
                print("API INTENT:", api_intent)
                print("CONTEXT:", context[:500])
                print("SOURCES:", sources)

            else:
                context, sources = retrieve_context(question, n_results=5)
        else:
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
            save_qa(
                question=question,
                answer=answer,
                language=language,
                sources=sources,
            )
        except Exception as error:
            print(f"CSV save error: {error}")

    sent_to_review = False
    review_case_id = None
    review_reason = None

    need_review, reason = should_send_to_review(
        answer=answer,
        context=context,
        sources=sources,
    )

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

        except Exception as error:
            print(f"Review case save error: {error}")

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

#take user sceenshots 
#Gemini vision take text from photo
#res go to base pipeline

from app.rag.image_analyzer import analyze_sceenshot

def process_user_image(
        image_bytes: bytes,
        caption: str = "",
        save_to_csv: bool = True,
        save_review_cases: bool = True,
        forced_language: str | None = None,
) -> dict:
    
    language = forced_language or "ru"
    
    #analyze photo
    try:
        image_info = analyze_sceenshot(image_bytes, language= language)
    except Exception as err:
        return {
            "success": False,
            "language": language,
            "question": caption or "[изображение]",
            "answer": f"Не удалось проанализировать изображение: {err}",
            "sources": [],
            "context": "",
            "sent_to_review": False,
            "review_case_id": None,
            "review_reason": None,
            "image_description": "",
        }
    
    extracted_text = image_info.get("extraced_text", "")
    search = image_info.get("search_query", "")
    description = image_info.get("description", "")

    #no text
    if not extracted_text and not search:
        no_text_answer = {
            "ru": "Не смог распознать текст на изображении. Попробуйте описать проблему текстом.",
            "uz": "Rasmdan matnni tanib bo'lmadi. Muammoni matn orqali tasvirlang.",
            "en": "Could not extract text from the image. Please describe the issue in text.",
        }
        return {
            "success": False,
            "language": language,
            "question": caption or "[изображение]",
            "answer": no_text_answer.get(language, no_text_answer["ru"]),
            "sources": [],
            "context": "",
            "sent_to_review": False,
            "review_case_id": None,
            "review_reason": None,
            "image_description": description,
        }
    
    
    #build question
    if caption:
        combined_question = f"{caption}\n\n[Текст с фото]: {extracted_text}"

    else:
        combined_question = extracted_text

    
    #rag pipeline
    rag_result = process_user_question(
        question=search or combined_question,
        save_to_csv=save_to_csv,
        save_case_for_review = save_case_for_review,
        forced_language=language,
    )

    #add description of photo
    if description:
        prefix_map = {
            "ru": f"🖼 \bНа скриншоте:\b {description}\n\n",
            "uz": f"🖼 \bSkrinshot:\b {description}\n\n",
            "en": f"🖼 \bScreenshot:\b {description}\n\n",
        }

        prefix = prefix_map.get(language, prefix_map["ru"])
        rag_result["answer"] = prefix + rag_result["answer"]

    rag_result["image_description"] = description
    return rag_result

from app.rag.image_analyzer import analyze_sceenshot

def process_user_image(
        image_bytes: bytes,
        caption: str ="",
        save_to_csv: bool = True,
        save_review_cases: bool = True,
        forced_language: str | None = None,
) -> dict:
    
    language = forced_language or "ru"

    #analyze photo
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

    #no text
    if not extracted_text and not search_query:
        no_text_answer = {
            "ru": "Не смог распознать текст на изображении. Опишите проблему текстом.",
            "uz": "Rasmdan matnni tanib bo'lmadi. Muammoni matn orqali tasvirlang.",
            "en": "Could not extract text from the image. Please describe the issue in text.",
        }
        return {
            "success": False,
            "language": language,
            "question": caption or "[изображение]",
            "answer": no_text_answer.get(language, no_text_answer["ru"]),
            "sources": [], "context": "",
            "sent_to_review": False,
            "review_case_id": None,
            "review_reason": None,
            "image_description": description,
        }
    
    combined_question = f"{caption}\n\n[Текст со скриншота]: {extracted_text}" if caption else extracted_text

    rag_result = process_user_question(
        question=search_query or combined_question,
        save_to_csv=save_to_csv,
        save_review_cases=save_review_cases,
        forced_language=language,
    )


    if description:
        prefix = {
            "ru": f"🖼 *На скриншоте:* {description}\n\n",
                  "uz": f"🖼 *Skrinshot:* {description}\n\n",
                  "en": f"🖼 *Screenshot:* {description}\n\n"}.get(language, "")
        rag_result["answer"] = prefix + rag_result["answer"]

    rag_result["image_description"] = description
    return rag_result
        

