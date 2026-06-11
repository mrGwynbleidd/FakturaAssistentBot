import json


def extract_json_from_context(api_context: str):
    if "RAW_JSON_RESULT:" in api_context:
        json_part = api_context.split("RAW_JSON_RESULT:", 1)[1].strip()
        json_part = json_part.split("INTERPRETATION_RULE:", 1)[0].strip()
    elif "JSON:" in api_context:
        json_part = api_context.split("JSON:", 1)[1].strip()
    else:
        return None

    # Сначала проверяем bool как текст
    lowered = json_part.lower()
    if lowered.startswith("true"):
        return True
    if lowered.startswith("false"):
        return False

    try:
        return json.loads(json_part)
    except Exception:
        return None


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




def format_company_check_from_context(api_context: str, language: str = "ru") -> str:
    data = extract_json_from_context(api_context)

    inn = ""
    if "USER_INN:" in api_context:
        inn = api_context.split("USER_INN:", 1)[1].split("\n", 1)[0].strip()

    if data is True:
        if language == "en":
            return f"✅ Company with INN {inn} is registered in Faktura.uz."
        if language == "uz":
            return f"✅ {inn} INN raqamli kompaniya Faktura.uz tizimida ro'yxatdan o'tgan."
        return f"✅ Компания с ИНН {inn} зарегистрирована в системе Faktura.uz."

    if data is False:
        if language == "en":
            return f"❌ Company with INN {inn} was not found in Faktura.uz."
        if language == "uz":
            return f"❌ {inn} INN raqamli kompaniya Faktura.uz tizimida topilmadi."
        return f"❌ Компания с ИНН {inn} не найдена в системе Faktura.uz."

    if isinstance(data, dict):
        pretty = json.dumps(data, ensure_ascii=False, indent=2)
        if language == "en":
            return f"Faktura API returned data for INN {inn}:\n\n{pretty}"
        if language == "uz":
            return f"Faktura API {inn} INN bo'yicha ma'lumot qaytardi:\n\n{pretty}"
        return f"Faktura API вернул данные по ИНН {inn}:\n\n{pretty}"

    return ""


def format_api_answer_direct(
    question: str,
    api_context: str,
    language: str = "ru",
) -> str:
    # БАГ 3 БЫЛ: api_context.islower() возвращает bool, not строку
    # БАГ 4 БЫЛ: format_company_check_from_context никогда не вызывалась
    if "GetDocumentTypes" in api_context or "document types" in api_context.lower():
        return format_document_types_from_context(api_context, language)

    if "CheckCompanyExist" in api_context or "USER_INN:" in api_context:
        return format_company_check_from_context(api_context, language)

    return ""