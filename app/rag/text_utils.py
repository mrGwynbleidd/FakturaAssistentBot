
import hashlib
import re

def clean_text(value: str | None) -> str:
    if not value:
        return ""
    
    return " ".join(str(value).replace("\x00", " ").split())

def safe_get(row: dict, keys: list[str], default: str="") -> str:
    for key in keys:
        value = row.get(key)
        if value is not None and str(value).strip():
            return clean_text(str(value))
        
        return default
    
def stable_hash(text: str, length: int = 16) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:length]

def make_id(prefix: str, text: str) -> str:
    return f"{prefix}_{stable_hash(text)}"

def tokenize(text: str) -> set[str]:
    text = clean_text(text).lower()
    tokens = re.findall(r"[a-zA-Zа-яА-ЯёЁўғқҳ0-9]+", text)
    return {token for token in tokens if len(token) >= 3}

def lexical_overlap_score(query: str, document: str) -> float:
    query_tokens = tokenize(query)
    document_tokens = tokenize(document)

    if not query_tokens or not document_tokens:
        return 0.0

    overlap = query_tokens.intersection(document_tokens)
    return len(overlap) / max(len(query_tokens), 1)


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


 

