import re

from app.faktura_api.endpoints import (
    get_document_types,
    get_document_creation_types,
    check_company_exists,
    get_employees,
)
from app.faktura_api.formatter import format_json_context


def extract_inn(question: str) -> str | None:
    # БАГ 1 БЫЛ: \d{90\b} — опечатка, никогда не матчило
    match = re.search(r"\b\d{9}\b", question)
    if match:
        return match.group(0)
    return None


def get_api_context(question: str, intent: str) -> tuple[str, list[dict]]:

    if intent == "get_document_types":
        data = get_document_types()
        context = format_json_context(data, title="Faktura API result: document types")
        return context, [{
            "source": "Faktura API: GetDocumentTypes",
            "source_type": "api",
            "api_intent": "get_document_types",
        }]

    if intent == "get_document_creation_types":
        data = get_document_creation_types()
        context = format_json_context(data, title="Faktura API result: document creation types")
        return context, [{
            "source": "Faktura API: GetDocumentCreationTypes",
            "source_type": "api",
            "api_intent": "get_document_creation_types",
        }]

    if intent == "check_company_exists":
        inn = extract_inn(question)

        if not inn:
            context = """
SOURCE: Faktura API
TITLE: INN check

RESULT:
Пользователь хочет проверить ИНН, но в вопросе не найден 9-значный ИНН.
Попроси пользователя отправить ИНН в формате 9 цифр.
""".strip()
            return context, [{
                "source": "Faktura API: CheckCompanyExist",
                "source_type": "api",
                "api_intent": "check_company_exists",
            }]

        # БАГ 2 БЫЛ: эта строка была вне if — выполнялась даже когда inn = None
        data = check_company_exists(inn)

        context = f"""
SOURCE: Faktura API
TITLE: Company existence check

API_METHOD:
GET /Api/CheckCompanyExist/{inn}

USER_INN:
{inn}

RAW_JSON_RESULT:
{data}

INTERPRETATION_RULE:
Если RAW_JSON_RESULT равен true — компания зарегистрирована в Faktura.uz.
Если RAW_JSON_RESULT равен false — компания не найдена или не зарегистрирована.
Если RAW_JSON_RESULT является объектом JSON — объясни поля простым языком.
""".strip()

        return context, [{
            "source": f"Faktura API: CheckCompanyExist/{inn}",
            "source_type": "api",
            "api_intent": "check_company_exists",
            "inn": inn,
        }]

    return "", []