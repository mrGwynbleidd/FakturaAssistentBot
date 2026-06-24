#shared text utility functions for cleaning, hashing, tokenizing, and scoring text
#used across rag loaders, index builder, and priority retriever

import hashlib
import re

#strips null bytes and collapses whitespace, returns empty string if value is falsy
#used throughout all loaders and cleaners
def clean_text(value: str | None) -> str:
    if not value:
        return ""
    
    return " ".join(str(value).replace("\x00", " ").split())

#returns the first non-empty value from a list of dict keys, cleaned
#used in admin_knowledge_loader to safely extract fields
def safe_get(row: dict, keys: list[str], default: str="") -> str:
    for key in keys:
        value = row.get(key)
        if value is not None and str(value).strip():
            return clean_text(str(value))
        
        return default
    
#returns a truncated sha256 hex digest of the text, used to create stable unique ids
def stable_hash(text: str, length: int = 16) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:length]

#creates a stable prefixed id from prefix and text hash
#used to generate chroma document ids for pdfs and knowledge entries
def make_id(prefix: str, text: str) -> str:
    return f"{prefix}_{stable_hash(text)}"

#splits text into a set of lowercase tokens of 3+ characters
#used in lexical_overlap_score
def tokenize(text: str) -> set[str]:
    text = clean_text(text).lower()
    tokens = re.findall(r"[a-zA-Zа-яА-ЯёЁўғқҳ0-9]+", text)
    return {token for token in tokens if len(token) >= 3}

#computes jaccard-like overlap ratio between query and document token sets
#returns a float 0-1 representing how many query tokens appear in the document
#used in priority_retriever.final_score
def lexical_overlap_score(query: str, document: str) -> float:
    query_tokens = tokenize(query)
    document_tokens = tokenize(document)

    if not query_tokens or not document_tokens:
        return 0.0

    overlap = query_tokens.intersection(document_tokens)
    return len(overlap) / max(len(query_tokens), 1)


#normalizes language string to standard codes ru/uz/en, defaults to ru if unknown
#used in priority_retriever.language_allowed and approved_loader
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
