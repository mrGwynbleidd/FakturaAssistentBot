# Detect whether a user question needs a live Faktura API call,
# and which specific intent it maps to.

import re


def should_use_faktura_api(question: str) -> bool:
    q = question.lower()
    # 32-char hex UID always implies a document lookup
    if re.search(r'\b[0-9a-fA-F]{32}\b', question):
        return True
    return any(kw in q for kw in _ALL_KEYWORDS)


def extract_uid(question: str) -> str | None:
    """Extract 32-char hex document UID (Faktura/Soliq document identifier)."""
    match = re.search(r'\b([0-9a-fA-F]{32})\b', question)
    return match.group(1) if match else None


def detect_api_intent(question: str) -> str | None:
    q = question.lower()

    # Document sync check — triggered by 32-char hex UID or explicit sync keywords
    if re.search(r'\b[0-9a-fA-F]{32}\b', question):
        return "check_document_sync"

    if _match(q, ["синхрониз", "солик статус", "soliq статус", "soliq status",
                   "статус в солик", "статус в soliq", "расхождени", "не совпадает статус",
                   "проверить статус документа", "sync document", "document sync"]):
        return "check_document_sync"

    # INN-based lookups — check most specific first
    if _match(q, ["плательщик ндс", "ндс плательщик", "nds payer", "является ли плательщиком ндс",
                   "платит ндс", "ндс платит"]):
        return "check_nds_payer"

    if _match(q, ["ндс код", "код ндс", "nds code", "vat code", "getndsvatcode"]):
        return "get_nds_vat_code"

    if _match(q, ["филиал", "filial", "branches", "getcompanybranchs"]):
        return "get_company_branches"

    if _match(q, ["сотрудник", "работник", "employee", "getemployees", "проверить сотрудника",
                   "список сотрудников"]):
        return "get_employees"

    if _match(q, ["роль", "роли", "role", "roles", "getcompanyroles"]):
        return "get_company_roles"

    if _match(q, ["икпу", "ikpu", "каталог товаров", "product catalog", "товар", "найти товар",
                   "поиск товара", "код товара"]):
        return "search_product_catalog"

    if _match(q, ["единиц", "измерени", "measurement", "getmeasurements", "единицы"]):
        return "get_measurements"

    if _match(q, ["статус документ", "document status", "getdocumentstatuses", "статусы документов"]):
        return "get_document_statuses"

    if _match(q, ["тип документа", "типы документов", "document types", "getdocumenttypes"]):
        return "get_document_types"

    if _match(q, ["типы создания", "creation types", "getdocumentcreationtypes"]):
        return "get_document_creation_types"

    # company info — broad INN queries go to full details if we have an INN
    if _match(q, ["информация о компании", "данные компании", "getcompanybasicdetails",
                   "название компании", "адрес компании", "директор", "подробнее о компании"]):
        return "get_company_details"

    # plain INN check — most common
    if _match(q, ["проверить инн", "проверь инн", "инн", "check company",
                   "компания зарегистрирована", "checkcompanyexist"]):
        return "check_company_exists"

    return None


# ── helpers ────────────────────────────────────────────────────────────────────

def _match(q: str, keywords: list[str]) -> bool:
    return any(kw in q for kw in keywords)


_ALL_KEYWORDS = [
    # INN / company
    "инн", "inn", "check company", "компания зарегистрирована",
    "информация о компании", "данные компании", "название компании",
    "ндс", "nds", "vat", "филиал", "filial", "branch",
    "сотрудник", "работник", "employee",
    "роль", "роли", "role",
    "икпу", "ikpu", "каталог товаров", "product catalog", "товар",
    # document
    "тип документа", "типы документов", "document type",
    "типы создания", "creation type",
    "статус документ", "document status",
    "единиц измерени", "measurement",
    # sync / soliq
    "синхрониз", "солик", "soliq", "расхождени", "не совпадает статус",
    "проверить статус документа", "sync document",
    # direct API mentions
    "api", "getdocumenttypes", "getdocumentcreationtypes", "getdocumentstatuses",
    "getcompanybasicdetails", "getemployees", "getcompanyroles",
    "checkcompanyexist", "getmeasurements", "getcompanybranchs",
    "getdocumentstatus", "getdocumentdetails",
]
