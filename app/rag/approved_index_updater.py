
from app.rag.approved_loader import load_approved_cases
from app.rag.chroma_client import get_or_create_collection, reset_collection
from app.rag.embedding import embed_texts
from app.rag.settings import COLLECTION_APPROVED
from app.rag.text_utils import clean_text, make_id, normalize_language

def build_approved_doc(case_id: str, question: str, answer: str, language: str = "ru", category: str = "review", source_type: str ="admin_review", source_id: str = "") -> dict:
    question = clean_text(question)
    answer = clean_text(answer)
    language = normalize_language(language)
    category = clean_text(category or "review")

    if not case_id:
        case_id = make_id("approved", question + answer)
    text = (
        "VERIFIED APPROVED CASE\n"
        f"Question: {question}\n"
        f"Approved answer: {answer}\n"
        f"Category: {category}"
    )
    return {
        "id": f"approved_{case_id}",
        "text": text,
        "metadata": {
            "source_type": "approved",
            "case_id": case_id,
            "language": language,
            "category": category,
            "source_id": source_id or case_id,
            "original_source_type": source_type,
            "question": question,
            "answer": answer,
            "priority": 100,
        },
    }


def add_approved_case_to_index(case_id: str, question: str, answer: str, language: str = "ru", category: str = "review", source_type: str = "admin_review", source_id: str = "") -> bool:
    if not question or not answer:
        return False
    
    collection = get_or_create_collection(COLLECTION_APPROVED)
    doc = build_approved_doc(case_id, question, answer, language, category, source_type, source_id)

    try:
        collection.delete(ids=[doc["id"]])
    except Exception:
        pass

    collection.add(
        ids=[doc["id"]],
        documents=[doc["text"]],
        metadatas=[doc["metadata"]],
        embeddings=embed_texts([doc["text"]]),
    )
    return True


def rebuild_approved_index() -> int:
    collection = reset_collection(COLLECTION_APPROVED)
    docs = load_approved_cases()

    if not docs:
        return 0
    
    texts = [doc["id"] for doc in docs]
    collection.add(
        ids=[doc["id"] for doc in docs],
        documents=texts,
        metadatas=[doc["metadata"] for doc in docs],
        embeddings=embed_texts(texts),
    )
    return len(docs)
