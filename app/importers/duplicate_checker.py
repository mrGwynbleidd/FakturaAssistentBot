
import csv
import re
from dataclasses import dataclass
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any

from app.importers.text_cleaner import clean_text

BASE_DIR = Path(__file__).resolve().parents[2]

APPROVED_CSV_PATH = BASE_DIR / "data" / "learning" / "approved.csv"

DUPLICATE_QUESTION_THRESHOLD = 0.92
DUPLICATE_ANSWER_THRESHOLD = 0.80

QUESTION_COLUMNS = [
    "question",
    "user_question",
    "client_question",
    "request",
    "message",
    "text",
    "ворос",
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


SOURCE_ID_COLUMNS = [
    "source_id",
    "ticket_id",
    "case_id",
    "id",
    "request_id",
    "appeal_id",
]

CASE_ID_COLUMNS = [
    "case_id",
    "id",
    "approved_id",
]

@dataclass
class ApprovedEntry:
    case_id: str
    source_id: str
    question: str
    answer: str
    raw: dict[str, Any]

@dataclass
class DuplicateCheckResult:
    is_duplicate: bool
    reason: str
    score: float
    matched_case_id: str = ""
    matched_source_id: str = ""
    matched_question: str = ""
    matched_answer: str = ""

def normalize_key(value: str | None) -> str:
    if not value:
        return ""
    
    return (
        str(value)
        .strip()
        .lower()
        .replace(" ", "_")
        .replace("-", "_")
    )

def find_column(fieldnames: list[str], candidates: list[str]) -> str | None:
    normalized_map = {
        normalize_key(fieldnames): fieldname
        for fieldname in fieldnames
    }

    for candidate in candidates:
        candidate_normalized = normalize_key(candidate)

        for normalized_fieldname, original_fieldname in normalized_map.items():
            if candidate_normalized in normalized_fieldname:
                return original_fieldname
            
    return None


def normalize_for_duplicate(text: Any) -> str:
    text = clean_text(text).lower()

    if not isinstance(text, str):
        return text

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


    text = re.sub(r"[^a-zа-яё0-9ўғқҳ\- ]+", " ", text, flags=re.IGNORECASE)
    text = " ".join(text.split())

    return text


def similarity(first: Any, second: Any) -> float:
    first_normalized= normalize_for_duplicate(first)
    second_normalized = normalize_for_duplicate(second)

    if not first_normalized or not second_normalized:
        return 0.0
    
    try:
        from rapidfuzz import fuzz

        return float(fuzz.token_set_ratio(first_normalized, second_normalized)) / 100.0
    except Exception:
        return SequenceMatcher(None, first_normalized, second_normalized).ratio()
    

def load_approved_entries(path: Path = APPROVED_CSV_PATH) -> list[ApprovedEntry]:
    if not path.exists():
        return []
    
    entries: list[ApprovedEntry] = []

    with open(path, mode="r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames or []


        if not fieldnames:
            return []
        
        case_id_column = find_column(fieldnames, CASE_ID_COLUMNS)
        source_id_column = find_column(fieldnames, SOURCE_ID_COLUMNS)
        question_column = find_column(fieldnames, QUESTION_COLUMNS)
        answer_column = find_column(fieldnames, ANSWER_COLUMNS)

        for row_index, row in enumerate(reader, start=1):
            case_id = clean_text(row.get(case_id_column, "")) if case_id_column else ""
            source_id = clean_text(row.get(source_id_column, "")) if source_id_column else ""
            question = clean_text(row.get(question_column, "")) if question_column else ""
            answer = clean_text(row.get(answer_column, "")) if answer_column else ""

            if not case_id:
                case_id = f"approved_row_{row_index}"

            if not question and not answer:
                continue

            entries.append(
                ApprovedEntry(
                    case_id=case_id,
                    source_id=source_id,
                    question=question,
                    answer=answer,
                    raw=row,
                )
            )
    
    return entries


def check_duplicate_in_approved(
        ticket: dict[str, Any],
        approved_csv_path: Path = APPROVED_CSV_PATH,

) -> DuplicateCheckResult:
    
    ticket_id = clean_text(ticket.get("ticket_id", ""))
    question = clean_text(ticket.get("question", ""))
    answer = clean_text(ticket.get("answer", ""))

    entries = load_approved_entries(approved_csv_path)

    if not entries:
        return DuplicateCheckResult(
            is_duplicate=False,
            reason="approved.csv_empty_or_not_found",
            score=0.0
        )
    
    for entry in entries:
        if ticket_id and entry.source_id and ticket_id == entry.source_id:
            return DuplicateCheckResult(
                is_duplicate=True,
                reason="same_ticket_id_or_source_id",
                score=1.0,
                matched_case_id=entry.case_id,
                matched_source_id=entry.source_id,
                matched_question=entry.question,
                matched_answer=entry.answer,
            )
    
    ticket_question_norm = normalize_for_duplicate(question)
    ticket_answer_norm = normalize_for_duplicate(answer)

    for entry in entries:
        entry_question_norm = normalize_for_duplicate(entry.question)
        entry_answer_norm = normalize_for_duplicate(entry.answer)

        if (
            ticket_question_norm
            and ticket_answer_norm
            and ticket_question_norm == entry_question_norm
            and ticket_answer_norm == entry_answer_norm
        ):
            return DuplicateCheckResult(
                is_duplicate=True,
                reason="same_question_and_answer",
                score=1.0,
                matched_case_id=entry.case_id,
                matched_source_id=entry.source_id,
                matched_question=entry.question,
                matched_answer=entry.answer,
            )
        
    best_score = 0.0
    best_entry: ApprovedEntry | None = None
    best_question_score = 0.0
    best_answer_score = 0.0

    for entry in entries:
        question_score = similarity(question, entry.question)
        answer_score = similarity(answer, entry.answer)

        combined_score = (question_score * 0.70) + (answer_score * 0.30)


        if combined_score > best_score:
            best_score = combined_score
            best_entry = entry
            best_question_score = question_score
            best_answer_score = answer_score

    if (
        best_entry
        and best_question_score >= DUPLICATE_QUESTION_THRESHOLD
        and best_answer_score >= DUPLICATE_ANSWER_THRESHOLD
    ):
        return DuplicateCheckResult(
            is_duplicate=True,
            reason="similar_question_and_answer",
            score=best_score,
            matched_case_id=best_entry.case_id,
            matched_source_id=best_entry.source_id,
            matched_question=best_entry.question,
            matched_answer=best_entry.answer,
        )
    
    if best_entry and best_question_score >= 0.96:
        return DuplicateCheckResult(
            is_duplicate=True,
            reason="very_similar_question",
            score=best_answer_score,
            matched_case_id=best_entry.case_id,
            matched_source_id=best_entry.source_id,
            matched_question=best_entry.question,
            matched_answer=best_entry.answer,
        )
    
    return DuplicateCheckResult(
        is_duplicate=False,
        reason="no_duplicate_found",
        score=best_score,
        matched_case_id=best_entry.case_id if best_entry else "",
        matched_source_id=best_entry.source_id if best_entry else "",
        matched_question=best_entry.question if best_entry else "",
        matched_answer=best_entry.answer if best_entry else "",
    )


def duplicate_result_to_dict(result: DuplicateCheckResult) -> dict[str, Any]:
    return {
        "is_duplicate": result.is_duplicate,
        "reason": result.reason,
        "score": round(result.score, 4),
        "matched_case_id": result.matched_case_id,
        "matched_source_id": result.matched_source_id,
        "matched_question": result.matched_question,
        "matched_answer": result.matched_answer,
    }