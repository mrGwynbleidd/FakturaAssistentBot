import json
from app.faktura_api.formatter import format_document_types

#take json from api context
def extract_json_from_context(api_context: str):
    if "RAW_JSON_RESULT:" in api_context:
        json_part = api_context.split("RAW_JSON_RESULT:", 1)[1].strip()
        json_part = json_part.split("INTERPRETATION_RULE:", 1)[0].strip()
    elif "JSON:" in api_context:
        json_part = api_context.split("JSON:", 1)[1].strip()
    else:
        return None
    
    #check bool as text
    lowered = json_part.lower()
    if lowered.startswith("true"):
        return True
    if lowered.startswith("false"):
        return False

    try:
        return json.loads(json_part)
    except Exception:
        return None

### What type of documents are avaiable in Faktura    
def format_document_types_from_context(api_context: str, language: str = "ru") -> str:
    data = extract_json_from_context(api_context)

    if not isinstance(data, list):
        return ""
    
    if language == "en":
        lines = ["Available document types in Faktura:"]
    elif language == "uz":
        lines = ["Faktura tizimida mavjud hujjat turlari:"]
    else:
        lines = ["В Faktura доступны следующие типы документов:"]

    for index, item in enumerate(data, start=1):
        description = item.get("description", "Без названия")
        code = item.get("code", "no_code")
        item_id = item.get("id", "")

        lines.append(f"{index}. {description} — code: {code}, id: {item_id}")

    return "\n".join(lines)

### INN check
def format_company_check_from_context(api_context: str, language: str = "ru") -> str:
    data = extract_json_from_context(api_context)

    inn = ""

    if "USER_INN:" in api_context:
        inn = api_context.split("USER_INN:", 1)[1].split("\n", 1)[0].strip()

    if data is True:
        if language == "en":
            return f"✅ According to Faktura API, company with INN {inn} is registered in Faktura.uz"
        if language == "uz":
            return f"✅ Faktura API natijasiga ko‘ra, {inn} INN raqamli kompaniya Faktura.uz tizimida ro‘yxatdan o‘tgan."
        return f"✅ По результату проверки через Faktura API компания с ИНН {inn} зарегистрирована в системе Faktura.uz."

    if data is False:
        if language == "en":
            return f"❌ According to Faktura API, company with INN {inn}, was not found or not registered in Faktura.uz"
        
        if language == "uz":
            return f"❌ Faktura API natijasiga ko‘ra, {inn} INN raqamli kompaniya topilmadi yoki Faktura.uz tizimida ro‘yxatdan o‘tmagan."
        
        return f"❌ По результату проверки через Faktura API компания с ИНН {inn} не найдена или не зарегистрирована в системе Faktura.uz."

    if isinstance(data, dict):
        pretty = json.dumps(data, ensure_ascii=False, indent=2)

        if language == "en":
            return f"Faktura API returned following data for INN {inn}:\n\n{pretty}"

        if language == "uz":
            return f"Faktura API {inn} INN bo‘yicha quyidagi ma’lumotlarni qaytardi:\n\n{pretty}"

        return f"Faktura API вернул следующие данные по ИНН {inn}:\n\n{pretty}"

    return ""
  
#try to form answer w/o LLM, if cannot sent quetion to Gemini
def format_api_answer_direct(
        question: str,
        api_context: str,
        language: str = "ru",
) -> str:
    if "GetDocumentTypes" in api_context or "document types" in api_context.islower():
        return format_document_types(api_context, language)
    
    if "CheckCompanyExist" in api_context or "USER_INN" in api_context:
        return format_company_check_from_context(api_context, language)
    
    return ""

