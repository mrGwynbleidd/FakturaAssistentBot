
from app.rag.chroma_client import get_or_create_collection
from app.rag.embedding import embed_text
from app.rag.text_utils import lexical_overlap_score, normalize_language
from app.rag.settings import (
    COLLECTION_APPROVED, COLLECTION_ADMIN_KNOWLEDGE, COLLECTION_PDF,
    APPROVED_DIRECT_THRESHOLD, ADMIN_DIRECT_THRESHOLD,
    APPROVED_CONTEXT_THRESHOLD, ADMIN_CONTEXT_THRESHOLD, PDF_CONTEXT_THRESHOLD,
    MAX_ADMIN_RESULTS, MAX_APPROVED_RESULTS, MAX_PDF_RESULTS,
)

def distance_to_similarity(distance: float | int | None) -> float:
    if distance is None:
        return 0.0
    
    try:
        similarity = 1.0 - float(distance)
    except Exception:
        return 0.0
    
    return max(0.0, min(1.0, similarity))


def language_allowed(metadata: dict, language: str | None) -> bool:
    if not language:
        return True
    
    language = normalize_language(language)
    doc_language = normalize_language(metadata.get("language", ""))
    if not doc_language:
        return True
    return doc_language in {language, "all"}

def source_bonus(source_type: str)-> float:
    if source_type == "approved":
        return 0.18
    
    if source_type == "admin_knowledge":
        return 0.12
    
    return 0.0


def final_score(query: str, document_text: str, metadata: dict, distance: float |int | None) -> float:
    semantic = distance_to_similarity(distance)
    lexical = lexical_overlap_score(query, document_text)
    bonus = source_bonus(str(metadata.get("source_type", "")))
    return min(1.0, (semantic *0.75) + (lexical *0.25) + bonus)

def search_collection(collection_name: str, query: str, k : int =5, language: str | None = None) -> list[dict]:
    try:
        collection = get_or_create_collection(collection_name)
        raw = collection.query(
            query_embeddings=[embed_text(query)],
            n_results=k,
            include=["documents", "metadatas", "distances"],
        )
    except Exception:
        return []
    
    ids = raw.get("ids", [[]])[0]
    documents = raw.get("documents", [[]])[0]
    metadatas = raw.get("metadatas", [[]])[0]
    distances = raw.get("distances", [[]])[0]

    results: list[dict] = []
    for item_id, document, metadata, distance in zip(ids, documents, metadatas, distances):
        metadata = metadata or {}
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



def search_approved_cases(query: str, language: str = "ru", k: int = MAX_APPROVED_RESULTS) -> list[dict]:
    return search_collection(COLLECTION_APPROVED, query, k=k, language=language)

def search_admin_knowledge(query: str, language: str = "ru", k: int = MAX_ADMIN_RESULTS) -> list[dict]:
    return search_collection(COLLECTION_ADMIN_KNOWLEDGE, query, k=k, language=language)


def search_pdf(query: str, language: str = "ru", k: int = MAX_PDF_RESULTS) -> list[dict]:
    return search_collection(COLLECTION_PDF, query, k=k, language=None)


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

def format_context(items: list[dict]) -> str:
    return "\n\n---\n\n\n".join(format_context_item(item, index) for index, item in enumerate(items, start=1))


def retrieve_priority_context(question: str, language: str = "ru") -> dict:
    approved = search_approved_cases(question, language=language)
    
    if approved and approved[0]["score"] >= APPROVED_DIRECT_THRESHOLD:
        best = approved[0]
        return {
            "mode": "direct_approved",
            "answer": best.get("metadata", {}).get("answer", ""),
            "context_text": format_context([best]),
            "sources":  [make_source(best)],
            "approved_results": approved,
            "admin_results": [],
            "pdf_results": [],
        }
    
    admin = search_admin_knowledge(question, language=language)
    if admin and admin[0]["score"] >= ADMIN_DIRECT_THRESHOLD:
        best = admin[0]
        return {
            "mode": "direct_admin_knowledge",
            "answer": best.get("metadata", {}).get("answer", ""),
            "context_text": format_context([best]),
            "sources": [make_source(best)],
            "approved_results": approved,
            "admin_knowledge": [],
            "pdf_results": [],
        }
    
    pdf = search_pdf(question, language=language)

    context_items: list[dict] = []
    context_items.extend(item for item in approved if item["score"] >= APPROVED_CONTEXT_THRESHOLD)
    context_items.extend(item for item in admin if item["score"] >= ADMIN_CONTEXT_THRESHOLD)
    context_items.extend(item for item in pdf if item["score"] >= PDF_CONTEXT_THRESHOLD)
    context_items.sort(key=lambda item: item["score"], reverse=True)
    context_items = context_items[:8]

    return{
        "mode": "llm_context",
        "answer": "",
        "context_text": format_context(context_items),
        "sources": [make_source(item) for item in context_items],
        "approved_results": approved,
        "admin_answer": admin,
        "pdf_results": pdf,
    }


def retrieve_context(question: str, language: str = "ru") -> str:
    return retrieve_priority_context(question, language=language).get("context_text", "")

def search_relevant_documents(question: str, language: str = "ru") -> list[dict]:
    return retrieve_priority_context(question, language=language).get("sources", [])

