
#import libs
import html
import re
from typing import Any

from app.importers.call_center_mapping import BAD_ANSWERS_PHRASES

EMPTY_VALUES = {
    "",
    "-",
    "--",
    "нет",
    "нет данных",
    "none",
    "null",
    "nan",
    "n/a",
}

SYSTEM_NOISE_PHRASES = [
    "с уважением",
    "служба поддержки",
    "автоматическое сообщение",
    "данное сообщение сформировано автоматически",
]

DIALOG_PREFIXES = [
    "оператор",
    "клиент:",
    "user:",
    "operator:",
    "support:",
]

def clean_text(value: Any) -> str:
    if value is None:
        return ""
    
    text = str(value)

    text = text.replace("\x00", " ")
    text = html.unescape(text)

    text = remove_html_tags(text)
    text = normalize_quotes(text)
    text = normalize_spaces(text)
    text = strip_system_noise(text)

    return text.strip()


def remove_html_tags(text: str)-> str:
    text = re.sub(r"<br\s*/?>", "\n", text, flags=re.IGNORECASE)
    text = re.sub(r"</p\s*>", "\n", text, flags=re.IGNORECASE)
    text = re.sub(r"<[^>]+", " ", text)

    return text

def normalize_quotes(text: str) -> str:
    replacements = {
        "«": '"',
        "»": '"',
        "“": '"',
        "”": '"',
        "‘": "'",
        "’": "'",
    }

    for old, new in replacements.items():
        text = text.replace(old, new)

    return text


def normalize_spaces(text: str)-> str:
    lines = []

    for line in text.splitlines():
        line = " ".join(line.split())

        if line:
            lines.append(line)

    return "\n".join(lines)

def remove_dialog_prefix(line: str)-> str:
    lowered = line.lower().strip()

    for prefix in DIALOG_PREFIXES:
        if lowered.startswith(prefix):
            return line[len(prefix):].strip()
        
    return line.strip()

def strip_system_noise(text: str)-> str:
    lines = text.splitlines()
    cleaned_lines = []

    for line in lines:
        line = line.strip()

        if not line:
            continue

        lowered = line.lower()

        if any(phrase in lowered for phrase in SYSTEM_NOISE_PHRASES):
            continue

        line = remove_dialog_prefix(line)

        if line:
            cleaned_lines.append(line)
    
    return "\n".join(cleaned_lines)


def is_empty_text(text: Any) -> bool:
    cleaned = clean_text(text).lower()

    return cleaned in EMPTY_VALUES

def normalize_language(value: Any) -> str:
    text = clean_text(value).lower()

    if not text:
        return "ru"
    if text in {"ru", "rus", "russian", "русский"}:
        return "ru"
    
    if text in {"uz", "uzb", "uzbek", "узбекский", "o'zbek", "ozbek"}:
        return "uz"
    
    if text in {"en", "eng", "english", "английский"}:
        return "en"
    
    return text

def normalize_status(value: Any) -> str:
    text = clean_text(value).lower()

    replacements = {
        "решён": "resolved",
        "решен": "resolved",
        "закрыт": "closed",
        "закрыто": "closed",
        "выполнен": "done",
        "обработан": "done",
        "hal qilindi": "resolved",
        "yopilgan": "closed",
        
    }

    return replacements.get(text, text)


def normalize_category(value: Any) -> str:
    text = clean_text(value).lower()

    if not text:
        return "general"
    
    replacemets = {
        "счет фактура": "invoice",
        "счёт фактура": "invoice",
        "счет-фактура": "invoice",
        "счёт-фактура": "invoice",
        "доверенность": "power_of_attorney",
        "акт": "act",
        "накладная": "waybill",
        "накладной": "waybill",
        "ттн": "waybill",
        "договор": "contract",
        "акт сверки": "reconciliation_act",
    }

    return replacemets.get(text, text)


def contains_bad_answer_phrase(text: Any) -> bool:
    cleaned = clean_text(text).lower()

    if not cleaned:
        return True
    
    for phrase in BAD_ANSWERS_PHRASES:
        if phrase.lower() in cleaned:
            return True
    
    return False


def contains_personal_data(text: Any) -> bool:

    cleaned = clean_text(text)

    patterns = [
        r"\b\d{9}\b",  # possible INN
        r"\+?\d[\d\s\-\(\)]{8,}\d",  # phone-like
        r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}",  # email
        r"\b[A-ZА-ЯЁ][a-zа-яё]+\s+[A-ZА-ЯЁ][a-zа-яё]+\s+[A-ZА-ЯЁ][a-zа-яё]+\b",  # possible full name
    ]

    for pattern in patterns:
        if re.search(pattern, cleaned):
            return True
        
    return False


def is_too_short_question(text: Any) -> bool:
    cleaned = clean_text(text)

    return len(cleaned) < 10


def is_too_short_answer(text: Any) -> bool:
    cleaned = clean_text(text)

    return len(cleaned) < 20

def normalize_ticket_fields(raw_ticket: dict[str, Any]) -> dict[str, str]:
    #normalize mapped ticket
    return {
        "ticket_id": clean_text(raw_ticket.get("ticket_id", "")),
        "created_at": clean_text(raw_ticket.get("created_at", "")),
        "language": normalize_language(raw_ticket.get("language", "")),
        "question": clean_text(raw_ticket.get("question", "")),
        "answer": clean_text(raw_ticket.get("answer", "")),
        "category": normalize_category(raw_ticket.get("category", "")),
        "status": normalize_status(raw_ticket.get("status", "")),
    }

def get_ticket_quality_reasons(ticket: dict[str, Any]) -> list[str]:
    #returns reason why ticket not ready approved

    normalized = normalize_ticket_fields(ticket)
    reasons = []

    if is_empty_text(normalized["question"]):
        reasons.append("empty_question")
    
    if is_empty_text(normalized["answer"]):
        reasons.append("empty_answer")
    
    if is_too_short_question(normalized["question"]):
        reasons.append("question_too_short")

    if is_too_short_answer(normalized["answer"]):
        reasons.append("answer_too_short")
    
    if contains_bad_answer_phrase(normalized["answer"]):
        reasons.append("bad_answer_phrase")
    
    if contains_personal_data(normalized["question"]):
        reasons.append("personal_data_in_question")
    
    if contains_personal_data(normalized["answer"]):
        reasons.append("personal_data_in_answer")

    return reasons
