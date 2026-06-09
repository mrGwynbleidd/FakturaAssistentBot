# import libs
import re
#import functions
from app.faktura_api.endpoints import(
    get_document_types,
    get_document_creation_types,
    check_company_exists,
)

from app.faktura_api.formatter import format_json_context

#search inn in question
def extract_inn(question: str) -> str | None:

    match = re.search(r"\b\d{9}\b}", question)

    if match:
        return match.group(0)
    
    return None

#get api-request and return context + source

def get_api_context(question: str, intent: str) -> tuple[str, list[dict]]:

    if intent == "get_document_types":
        data = get_document_types()

        context = format_json_context(
            data,
            title= "Faktura API result: document types",
        )

        return context, [
            {
                "source": "Faktura API: GetDocumentTypes",
                "source_type": "api",
                "api_intent": "get_document_types"
            }
        ]
    
    if intent == "get_document_creaction_types":
        data = get_document_creation_types()

        context = format_json_context(
            data,
            title="Faktura API result: document creation types",
        )

        return context, [
            {
                "source": "Faktura API GetDocumentCreationTypes",
                "source_type": "api",
                "api_intent": "get_document_creation_types",
            }
        ]
    
    if intent =="check_company_exists":
        inn = extract_inn(question)

        if not inn:
            context = """
SOURCE: Faktura API
TITLE: INN check

RESULT:
Пользователь хочет проверить ИНН, но в вопросе не найден 9-значный ИНН.
Попроси пользователя отправить ИНН в формате 9 цифр.
""".strip()

            return context, [
                {
                    "source": "Faktura API: CheckCompanyExist",
                    "source_type": "api",
                    "api_intent": "check_company_exists",
                }
            ]
            
        
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
Если RAW_JSON_RESULT равен true, значит компания с этим ИНН зарегистрирована в системе Faktura.uz.
Если RAW_JSON_RESULT равен false, значит компания с этим ИНН не найдена или не зарегистрирована в системе Faktura.uz.
Если RAW_JSON_RESULT является объектом JSON, объясни его поля пользователю простым языком.
""".strip()

        return context, [
            {
            "source": f"Faktura API: CheckCompanyExist/{inn}",
            "source_type": "api",
            "api_intent": "check_company_exists",
            "inn": inn,
            }
        ]
    
    return "", []


