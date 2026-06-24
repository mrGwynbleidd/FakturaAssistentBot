#loads approved Q&A pairs from approved.csv and converts them to chroma document dicts
#handles flexible column naming and filters out non-approved rows
#used in index_builder.build_approved_index

import csv
import hashlib
from pathlib import Path

from app.rag.settings import APPROVED_CSV_PATH

#keyword lists for fuzzy column detection — tries each keyword against csv headers
QUESTION_KEYWORDS = [
    "question",
    "user_question",
    "query",
    "request",
    "input",
    "вопрос",
    "запрос",
    "сообщение",
    "savol",
    "surov",
    "so'rov",
    "murojaat",
]

ANSWER_KEYWORDS = [
    "approved_answer",
    "answer",
    "admin_answer",
    "correct_answer",
    "bot_answer",
    "reply",
    "response",
    "ответ",
    "правильный",
    "javob",
    "tasdiqlangan",
]

STATUS_KEYWORDS = [
    "status",
    "статус",
    "holat",
]

LANGUAGE_KEYWORDS = [
    "language",
    "lang",
    "язык",
    "til",
]

CATEGORY_KEYWORDS = [
    "category",
    "topic",
    "категория",
    "тема",
    "kategoriya",
    "mavzu",
]

ID_KEYWORDS = [
    "case_id",
    "id",
    "approved_id",
    "review_id",
]


#strips null bytes and collapses whitespace in a cell value
def clean_text(value: str | None) -> str:
    if not value:
        return ""

    return " ".join(str(value).replace("\x00", " ").split())


#returns a truncated sha256 hex digest for generating stable row ids
def stable_hash(text: str, length: int = 16) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:length]


#normalizes a column name to lowercase with underscores for comparison
def normalize_key(key: str | None) -> str:
    if not key:
        return ""

    return str(key).strip().lower().replace(" ", "_")


#maps language aliases to standard codes ru/uz/en
def normalize_language(value: str | None) -> str:
    value = clean_text(value).lower()

    if not value:
        return "ru"

    if value in {"russian", "русский", "rus"}:
        return "ru"

    if value in {"uzbek", "узбекский", "uz"}:
        return "uz"

    if value in {"english", "английский", "en"}:
        return "en"

    return value


#scans fieldnames list for the first header that contains any of the keywords
#returns the original header name or None if not found
#used in row_to_document to locate question/answer/status columns
def find_column(fieldnames: list[str], keywords: list[str]) -> str | None:
    normalized_map = {
        normalize_key(fieldname): fieldname
        for fieldname in fieldnames
    }

    for keyword in keywords:
        keyword_normalized = normalize_key(keyword)

        for normalized_fieldname, original_fieldname in normalized_map.items():
            if keyword_normalized in normalized_fieldname:
                return original_fieldname

    return None


#returns cleaned cell value for a given column, or default if column is None
def get_value(row: dict, column: str | None, default: str = "") -> str:
    if not column:
        return default

    return clean_text(row.get(column, default))


#returns all non-empty cleaned cell values from a row as a list
#used as fallback when column names cannot be detected
def get_first_non_empty_values(row: dict) -> list[str]:
    values = []

    for value in row.values():
        value = clean_text(value)

        if value:
            values.append(value)

    return values


#converts a single csv row to a chroma document dict
#uses keyword-based column detection with fallback to positional values
#returns None if question or answer cannot be extracted or row status is not approved
def row_to_document(
    row: dict,
    row_number: int,
    fieldnames: list[str],
) -> dict | None:
    question_column = find_column(fieldnames, QUESTION_KEYWORDS)
    answer_column = find_column(fieldnames, ANSWER_KEYWORDS)
    status_column = find_column(fieldnames, STATUS_KEYWORDS)
    language_column = find_column(fieldnames, LANGUAGE_KEYWORDS)
    category_column = find_column(fieldnames, CATEGORY_KEYWORDS)
    id_column = find_column(fieldnames, ID_KEYWORDS)
    
    question = get_value(row, question_column)
    answer = get_value(row, answer_column)

    #fallback: if column names are completely non-standard, use first two non-empty values
    if not question or not answer:
        values = get_first_non_empty_values(row)

        if len(values) >= 2:
            if not question:
                question = values[0]

            if not answer:
                answer = values[1]

    if not question or not answer:
        print(
            f"Skipped approved row {row_number}: "
            f"cannot detect question/answer columns"
        )
        return None

    status = get_value(row, status_column, "approved").lower()

    #skip rows with explicit non-approved status
    if status and status not in {
        "approved",
        "active",
        "yes",
        "true",
        "ok",
        "1",
        "одобрено",
        "активно",
        "tasdiqlangan",
    }:
        return None

    case_id = get_value(row, id_column)

    #generate stable id from content if no id column found
    if not case_id:
        case_id = "approved_" + stable_hash(question + answer)

    language = normalize_language(
        get_value(row, language_column, "ru")
    )

    category = get_value(row, category_column, "approved")

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
            "question": question,
            "answer": answer,
            "priority": 100,
        },
    }


#reads approved.csv and returns a list of chroma-ready document dicts
#skips missing file, empty files, and invalid rows silently
#used in index_builder.build_approved_index and approved_index_updater.rebuild_approved_index
def load_approved_cases(path: Path = APPROVED_CSV_PATH) -> list[dict]:
    if not path.exists():
        print(f"Approved CSV not found: {path}")
        return []

    documents: list[dict] = []

    with open(path, mode="r", encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)
        fieldnames = reader.fieldnames or []

        print("Approved CSV columns:", fieldnames)

        if not fieldnames:
            print("Approved CSV is empty or has no header.")
            return []

        for row_number, row in enumerate(reader, start=1):
            document = row_to_document(
                row=row,
                row_number=row_number,
                fieldnames=fieldnames,
            )

            if document:
                documents.append(document)

    print(f"Approved cases loaded: {len(documents)}")

    return documents
