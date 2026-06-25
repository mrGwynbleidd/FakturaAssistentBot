#RAG retrieval pipeline — searches approved cases, admin knowledge, and PDF chunks
#returns either a direct answer (high confidence) or context text for LLM generation
#used in bot_engine.py step 2

import logging
log = logging.getLogger("bot.retriever")

from app.rag.chroma_client import get_or_create_collection
from app.rag.embedding import embed_text
from app.rag.text_utils import lexical_overlap_score, normalize_language
from app.rag.settings import (
    COLLECTION_APPROVED, COLLECTION_ADMIN_KNOWLEDGE, COLLECTION_PDF,
    APPROVED_DIRECT_THRESHOLD, ADMIN_DIRECT_THRESHOLD,
    APPROVED_CONTEXT_THRESHOLD, ADMIN_CONTEXT_THRESHOLD, PDF_CONTEXT_THRESHOLD,
    MAX_ADMIN_RESULTS, MAX_APPROVED_RESULTS, MAX_PDF_RESULTS,
)


#converts chroma cosine distance to a 0-1 similarity score, returns 0.0 on error
def distance_to_similarity(distance: float | int | None) -> float:
    if distance is None:
        return 0.0
    try:
        similarity = 1.0 - float(distance)
    except Exception:
        return 0.0
    return max(0.0, min(1.0, similarity))


#returns true if document language matches the query language or is unrestricted
#used in search_collection to filter results by language
def language_allowed(metadata: dict, language: str | None) -> bool:
    if not language:
        return True
    language = normalize_language(language)
    doc_language = normalize_language(metadata.get("language", ""))
    if not doc_language:
        return True
    return doc_language in {language, "all"}


#returns a score bonus based on source type — approved cases get highest bonus
#used in final_score
def source_bonus(source_type: str) -> float:
    if source_type == "approved":
        return 0.18
    if source_type == "admin_knowledge":
        return 0.12
    return 0.0


#computes combined score from semantic similarity, lexical overlap, and source bonus
#used in search_collection to rank results
def final_score(query: str, document_text: str, metadata: dict, distance: float | int | None) -> float:
    semantic = distance_to_similarity(distance)
    lexical = lexical_overlap_score(query, document_text)
    bonus = source_bonus(str(metadata.get("source_type", "")))
    return min(1.0, (semantic * 0.75) + (lexical * 0.25) + bonus)


#queries a named chroma collection and returns ranked result dicts with scores
#used by search_approved_cases, search_admin_knowledge, search_pdf
def search_collection(collection_name: str, query: str, k: int = 5, language: str | None = None) -> list[dict]:
    try:
        collection = get_or_create_collection(collection_name)
        raw = collection.query(
            query_embeddings=[embed_text(query)],
            n_results=k,
            include=["documents", "metadatas", "distances"],
        )
    except Exception as e:
        log.warning(f"  [CHROMA] {collection_name} — ошибка запроса: {e}")
        return []

    ids = raw.get("ids", [[]])[0]
    documents = raw.get("documents", [[]])[0]
    metadatas = raw.get("metadatas", [[]])[0]
    distances = raw.get("distances", [[]])[0]

    results: list[dict] = []
    for item_id, document, metadata, distance in zip(ids, documents, metadatas, distances):
        metadata = metadata or {}
        #skip results in the wrong language
        if not language_allowed(metadata, language):
            continue
        semantic_score = distance_to_similarity(distance)
        lexical_score = lexical_overlap_score(query, document)
        score = final_score(query, document, metadata, distance)
        results.append({
            "id": item_id,
            "text": document,
            "metadata": metadata,
            "distance": distance,
            "semantic_score": semantic_score,
            "lexical_score": lexical_score,
            "score": score,
            "source_type": metadata.get("source_type", ""),
        })

    results.sort(key=lambda item: item["score"], reverse=True)
    return results


#searches approved cases collection, returns ranked list of result dicts
def search_approved_cases(query: str, language: str = "ru", k: int = MAX_APPROVED_RESULTS) -> list[dict]:
    return search_collection(COLLECTION_APPROVED, query, k=k, language=language)


#searches admin knowledge collection, returns ranked list of result dicts
def search_admin_knowledge(query: str, language: str = "ru", k: int = MAX_ADMIN_RESULTS) -> list[dict]:
    return search_collection(COLLECTION_ADMIN_KNOWLEDGE, query, k=k, language=language)


#searches pdf collection without language filter, returns ranked list of result dicts
def search_pdf(query: str, language: str = "ru", k: int = MAX_PDF_RESULTS) -> list[dict]:
    return search_collection(COLLECTION_PDF, query, k=k, language=None)


#builds a flat source dict from a result item for returning to bot_engine
#used in retrieve_priority_context
def make_source(item: dict) -> dict:
    metadata = item.get("metadata", {})
    if not isinstance(metadata, dict):
        return metadata
    return {
        "source_type": item.get("source_type", ""),
        "score": round(float(item.get("score", 0)), 4),
        "semantic_score": round(float(item.get("semantic_score", 0)), 4),
        "lexical_score": round(float(item.get("lexical_score", 0)), 4),
        "case_id": metadata.get("knowledge_id", ""),
        "knowledge_id": metadata.get("knowledge_id", ""),
        "file_name": metadata.get("file_name", ""),
        "category": metadata.get("category", ""),
        "question": metadata.get("question", ""),
    }


#formats a single result item as a labeled text block for LLM context
#used in format_context
def format_context_item(item: dict, index: int) -> str:
    metadata = item.get("metadata", {})
    source_type = item.get("source_type", "")
    title_parts = [f"#{index}", f"source_type={source_type}", f"score={item.get('score', 0):.3f}"]
    if not isinstance(metadata, dict):
        return metadata
    if metadata.get("case_id"):
        title_parts.append(f"case_id={metadata.get('case_id')}")
    if metadata.get("knowledge_id"):
        title_parts.append(f"knowledge_id={metadata.get('knowledge_id')}")
    if metadata.get("file_name"):
        title_parts.append(f"file={metadata.get('file_name')}")
    return "[" + " | ".join(title_parts) + "]\n" + item.get("text", "")


#joins formatted context items into a single string separated by dividers
#used in retrieve_priority_context
def format_context(items: list[dict]) -> str:
    return "\n\n---\n\n\n".join(format_context_item(item, index) for index, item in enumerate(items, start=1))


#logs the top n results from a search to the debug logger
#used in retrieve_priority_context for diagnostics
def _log_top(label: str, results: list[dict], n: int = 3) -> None:
    if not results:
        log.info(f"  [{label}] нет результатов")
        return
    for i, r in enumerate(results[:n], 1):
        src = r.get("source_type", "")
        score = r.get("score", 0)
        sem = r.get("semantic_score", 0)
        lex = r.get("lexical_score", 0)
        q = (r.get("metadata", {}) or {}).get("question", r.get("text", ""))[:60]
        log.info(f"  [{label}] #{i} score={score:.3f} sem={sem:.3f} lex={lex:.3f} type={src} | {q}")

from app.rag.answer_adapter import adapt_answer

# score above which we skip gemini adaptation and return the approved answer as-is
_ADAPT_SKIP_THRESHOLD = 0.95

def normalize(text: str) -> str:
    return " ".join((text or "").lower().split())

# decides whether to return the approved answer directly or adapt it with gemini
# skips adaptation when: exact text match OR score is very high (>= _ADAPT_SKIP_THRESHOLD)
# otherwise calls adapt_answer to trim irrelevant parts and rephrase for the current question
def resolve_direct_answer(question: str, best: dict, language: str) -> str:
    metadata = best.get("metadata", {}) or {}
    approved_answer = metadata.get("answer", "")
    approved_question = metadata.get("question", "")
    score = float(best.get("score", 0))

    # exact same question — no adaptation needed
    if approved_question and normalize(question) == normalize(approved_question):
        log.info(f"  ✏️  resolve_direct: точное совпадение вопросов — возвращаем напрямую")
        return approved_answer

    # very high confidence — question is semantically identical, skip gemini call
    if score >= _ADAPT_SKIP_THRESHOLD:
        log.info(f"  ✏️  resolve_direct: score={score:.3f} >= {_ADAPT_SKIP_THRESHOLD} — пропускаем адаптацию")
        return approved_answer

    # similar but not identical — adapt the answer to the actual question
    log.info(f"  ✏️  resolve_direct: score={score:.3f} — запускаем адаптацию через Gemini")
    return adapt_answer(
        user_question=question,
        approved_question=approved_question,
        approved_answer=approved_answer,
        pdf_context="",
        language=language,
    )


#main retrieval function: approved → admin_knowledge → pdf
#returns dict with mode, answer (for direct hits), context_text, and sources
#used in bot_engine.process_user_question
def retrieve_priority_context(question: str, language: str = "ru") -> dict:
    log.info(f"🔍 RAG поиск | язык={language} | вопрос: {question[:70]}")
    log.info(f"  Пороги: approved_direct={APPROVED_DIRECT_THRESHOLD} admin_direct={ADMIN_DIRECT_THRESHOLD}")

    # ── 1. approved cases ──────────────────────────────────────────────────────
    approved = search_approved_cases(question, language=language)
    log.info(f"  [approved] найдено {len(approved)} результатов")
    _log_top("approved", approved)

    #return direct answer if top approved result exceeds the direct threshold
    if approved and approved[0]["score"] >= APPROVED_DIRECT_THRESHOLD:
        best = approved[0]
        log.info(f"  ✅ ПРЯМОЙ ОТВЕТ из approved (score={best['score']:.3f} >= {APPROVED_DIRECT_THRESHOLD})")
        return {
            "mode": "direct_approved",
            #"answer": best.get("metadata", {}).get("answer", ""),
            "answer": resolve_direct_answer(question,best, language),
            "context_text": format_context([best]),
            "sources": [make_source(best)],
            "approved_results": approved,
            "admin_results": [],
            "pdf_results": [],
        }

    # ── 2. admin knowledge ─────────────────────────────────────────────────────
    admin = search_admin_knowledge(question, language=language)
    log.info(f"  [admin_knowledge] найдено {len(admin)} результатов")
    _log_top("admin", admin)

    #return direct answer if top admin knowledge result exceeds the direct threshold
    if admin and admin[0]["score"] >= ADMIN_DIRECT_THRESHOLD:
        best = admin[0]
        log.info(f"  ✅ ПРЯМОЙ ОТВЕТ из admin_knowledge (score={best['score']:.3f} >= {ADMIN_DIRECT_THRESHOLD})")
        return {
            "mode": "direct_admin_knowledge",
            #"answer": best.get("metadata", {}).get("answer", ""),
            "answer": resolve_direct_answer(question, best, language),
            "context_text": format_context([best]),
            "sources": [make_source(best)],
            "approved_results": approved,
            "admin_knowledge": [],
            "pdf_results": [],
        }

    # ── 3. PDF ─────────────────────────────────────────────────────────────────
    pdf = search_pdf(question, language=language)
    log.info(f"  [pdf] найдено {len(pdf)} результатов")
    _log_top("pdf", pdf)

    # ── 4. build context for LLM from all sources above their thresholds ───────
    context_items: list[dict] = []
    context_items.extend(item for item in approved if item["score"] >= APPROVED_CONTEXT_THRESHOLD)
    context_items.extend(item for item in admin if item["score"] >= ADMIN_CONTEXT_THRESHOLD)
    context_items.extend(item for item in pdf if item["score"] >= PDF_CONTEXT_THRESHOLD)
    context_items.sort(key=lambda item: item["score"], reverse=True)
    #cap context at 8 fragments
    context_items = context_items[:8]

    if context_items:
        log.info(f"  📄 Контекст для LLM: {len(context_items)} фрагментов — " +
                 ", ".join(f"{r.get('source_type','?')}({r.get('score',0):.2f})" for r in context_items))
    else:
        log.info(f"  ⚠️  Контекст пустой — все результаты ниже порогов")

    return {
        "mode": "llm_context",
        "answer": "",
        "context_text": format_context(context_items),
        "sources": [make_source(item) for item in context_items],
        "approved_results": approved,
        "admin_answer": admin,
        "pdf_results": pdf,
    }


#compatibility wrapper — returns only context_text string
#used in rag/retriever.py
def retrieve_context(question: str, language: str = "ru") -> str:
    return retrieve_priority_context(question, language=language).get("context_text", "")


#compatibility wrapper — returns only sources list
#used in rag/retriever.py
def search_relevant_documents(question: str, language: str = "ru") -> list[dict]:
    return retrieve_priority_context(question, language=language).get("sources", [])
