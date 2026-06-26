
import csv
import sys
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any

BASE_DIR = Path(__file__).resolve().parent
APPROVED_CSV_PATH = BASE_DIR / "data" / "learning" / "approved.csv"

DIRECT_THRESHOLD = 0.76

QUESTION_COLUMNS = [
    "question",
    "user_question",
    "client_question",
    "request",
    "message",
    "text",
    "вопрос",
    "вопрос клиента",
    "savol",
    "murojaat",
]

ANSWER_COLUMNS = [
    "approved_answer",
    "answer",
    "admin_answer",
    "operator_answer",
    "reply",
    "response",
    "ответ",
    "ответ оператора",
    "javob",
]

CASE_ID_COLUMNS = [
    "case_id",
    "id",
    "approved_id",
    "source_id",
]

def clean_text(value: Any) -> str:
    if value is None:
        return ""
    
    return " ".join(str(value).replace("\x00", " ").split())


def normalize_key(value: Any) -> str:
    return (
        clean_text(value)
        .lower()
        .replace(" ", "_")
        .replace("-", "_")
        .strip()
    )

def find_column(fieldnames: list[str], candidates: list[str]) -> str | None:
    normalized_map = {
        normalize_key(fieldname): fieldname
        for fieldname in fieldnames
    }

    for candidate in candidates:
        candidate_normalized = normalize_key(candidate)

        for normalized_fieldname, origianl_fieldname in normalized_map.items():
            if candidate_normalized == normalized_fieldname:
                return origianl_fieldname
            
    for candidate in candidates:
        candidate_normalized = normalize_key(candidate)

        for normalized_fieldname, origianl_fieldname in normalized_map.items():
            if candidate_normalized in normalized_fieldname:
                return origianl_fieldname
    
    return None


def normalize_for_match(text: Any) -> str:
    text = clean_text(text).lower()

    replacements = {
        "счёт": "счет",
        "счет фактура": "счет-фактура",
        "счёт фактура": "счет-фактура",
        "счетфактура": "счет-фактура",
        "роуминг": "roaming",
        "руминг": "roaming",
        "инн": "inn",
        "эдо": "edo",
    }

    for old, new in replacements.items():
        text = text.replace(old, new)

    return " ".join(text.split())


def similarity(first: Any, second: Any) -> float:
    first_normalized = normalize_for_match(first)
    second_normalized = normalize_for_match(second)

    if not first_normalized or not second_normalized:
        return 0.0
    
    try:
        from rapidfuzz import fuzz

        return float(fuzz.token_set_ratio(first_normalized, second_normalized)) / 100.0
    except Exception:
        return SequenceMatcher(None, first_normalized, second_normalized).ratio()
    

def load_approved_rows() -> list[dict[str, str]]:
    if not APPROVED_CSV_PATH.exists():
        print(f"approved.csv not found: {APPROVED_CSV_PATH}")
        return []
    
    with open(APPROVED_CSV_PATH, mode="r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames or []

        print("Approved CSV:", APPROVED_CSV_PATH)
        print("Columns:", fieldnames)


        if not fieldnames:
            return []
        
        question_column = find_column(fieldnames, QUESTION_COLUMNS)
        answer_column = find_column(fieldnames, ANSWER_COLUMNS)
        case_id_column = find_column(fieldnames, CASE_ID_COLUMNS)

        print("Detected question column:", question_column)
        print("Detected answer column:", answer_column)
        print("Detected case_id/source_id column:", case_id_column)

        rows = []

        for index, row in enumerate(reader, start=1):
            question = clean_text(row.get(question_column, "")) if question_column else ""
            answer = clean_text(row.get(answer_column, "")) if answer_column else ""
            case_id = clean_text(row.get(case_id_column, "")) if case_id_column else ""

            if not question or not answer:
                continue

            rows.append(
                {
                    "case_id": case_id,
                    "question": question,
                    "answer": answer,

                }
            )
        
        return rows
    

def find_best_match(query: str) -> dict[str, Any] | None:
    rows =  load_approved_rows()

    print("Approved rows loaded:", len(rows))

    if not rows:
        return None
    
    best_row = None
    best_score = 0.0

    for row in rows:
        score = similarity(query, row["question"])

        if score > best_score:
            best_score = score
            best_row = row
        
    if not best_row:
        return None
    

    return {
        "case_id": best_row["case_id"],
        "question": best_row["question"],
        "answer": best_row["answer"],
        "score": best_score,
        "direct": best_score >= DIRECT_THRESHOLD,
    }


def main() -> None:

    if len(sys.argv) < 2:
        print('Usage: python debug_approved_matcher.py "your question"')
        return
    
    query = " ".join(sys.argv[1:])

    print("\nQUERY:")
    print(query)

    result = find_best_match(query)

    if not result:
        print("\nRESULT:")
        print("found: False")
        return
    
    print("\nRESULT:")
    print("found:", True)
    print("direct:", result["direct"])
    print("score:", round(result["score"], 4))
    print("case_id:", result["case_id"])

    print("\nMATCHED QUESTION:")
    print(result["question"])

    print("\nANSWER")
    print(result["answer"])


if __name__ == "__main__":
    main()