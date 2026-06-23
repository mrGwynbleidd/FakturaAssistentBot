# """
# Load admin Q/A from data/admin/admin_knowledge.csv for indexing into ChromaDB.
# source_type = "admin_knowledge"  (highest retrieval priority)
# """

# import csv
# from pathlib import Path



# BASE_DIR = Path(__file__).resolve().parents[2]
# ADMIN_KNOWLEDGE_PATH = BASE_DIR / "data" / "admin" / "admin_knowledge.csv"


# def load_admin_knowledge() -> list[dict]:
#     if not ADMIN_KNOWLEDGE_PATH.exists():
#         return []

#     documents = []

#     with open(ADMIN_KNOWLEDGE_PATH, mode="r", encoding="utf-8-sig", newline="") as f:
#         reader = csv.DictReader(f)

#         for row in reader:
#             status = row.get("status", "approved").strip().lower()
#             if status not in {"approved", "active"}:
#                 continue

#             question = row.get("question", "").strip()
#             answer = row.get("answer", "").strip()
#             if not question or not answer:
#                 continue

#             knowledge_id = row.get("knowledge_id", "").strip()
#             language = row.get("language", "ru").strip()
#             category = row.get("category", "general").strip()

#             text = f"User question: {question}\n\nCorrect answer: {answer}".strip()

#             documents.append({
#                 "source": f"admin_knowledge:{knowledge_id}",
#                 "text": text,
#                 "metadata": {
#                     "source": f"admin_knowledge:{knowledge_id}",
#                     "source_type": "admin_knowledge",
#                     "language": language,
#                     "category": category,
#                 },
#             })

#     return documents



import csv
from pathlib import Path

from app.rag.settings import ADMIN_KNOWLEDGE_CSV_PATH
from app.rag.text_utils import safe_get, make_id, normalize_language


def load_admin_knowledge(path: Path = ADMIN_KNOWLEDGE_CSV_PATH) -> list[dict]:

    if not path.exists():
        return []
    
    rows: list[dict] = []
    with open(path, mode="r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)

        for row in reader:
            status = safe_get(row, ["status"], "approved").lower()

            if status and status not in {"approved", "active", "yes", "true"}:
                continue

            question = safe_get(row, ["question", "user_question", "query"])
            answer = safe_get(row, ["answer", "admin_answer", "approved_answer"])

            if not question or not answer:
                continue

            knowledge_id = safe_get(row, ["knowledge_id", "id"])
            if not knowledge_id:
                knowledge_id = make_id("knowledge", question + answer)

            language = normalize_language(safe_get(row, ["language", "lang"], "ru"))
            category = safe_get(row, ["category", "topic"], "admin_knowledge")

            tags = safe_get(row, ["tags"], "")

            document_text = (
                "ADMIN KNOWLEDGE\n"
                f"Question: {question}\n"
                f"Answer: {answer}\n"
                f"Category: {category}\n"
                f"Tags: {tags}"
            )

            rows.append({
                "id": f"admin_{knowledge_id}",
                "text": document_text,
                "metadata": {
                    "source_type": "admin_knowledge",
                    "knowledge_id": knowledge_id,
                    "language": language,
                    "category": category,
                    "tags": tags,
                    "question": question,
                    "answer": answer,
                    "priority": 90,
                },
            })

    return rows