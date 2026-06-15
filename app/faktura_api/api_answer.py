import re
import json
import logging

from app.faktura_api.endpoints import (
    check_company_exists,
    get_company_details,
    check_nds_payer,
    get_nds_vat_code,
    get_employees,
    get_company_roles,
    get_company_branches,
    search_product_catalog,
    get_document_types,
    get_document_creation_types,
    get_document_statuses,
    get_measurements,
    get_document_status,
    get_document_details,
)
from app.faktura_api.formatter import format_json_context
from app.faktura_api.router import extract_uid

log = logging.getLogger("bot")


def extract_inn(question: str) -> str | None:
    """Extract 9-digit INN from question text."""
    match = re.search(r"\b\d{9}\b", question)
    return match.group(0) if match else None


def extract_ikpu(question: str) -> str | None:
    """Extract IKPU code (typically 17 digits) from question text."""
    match = re.search(r"\b\d{7,17}\b", question)
    return match.group(0) if match else None


def _no_inn_context(hint: str = "") -> tuple[str, list[dict]]:
    msg = (
        "Пользователь хочет получить информацию по ИНН, "
        "но 9-значный ИНН в вопросе не найден. "
        f"{hint}"
        "Попроси пользователя отправить ИНН в формате 9 цифр."
    )
    return msg, [{"source": "Faktura API", "source_type": "api"}]


def _make_source(label: str, intent: str, **extra) -> dict:
    return {"source": f"Faktura API: {label}", "source_type": "api",
            "api_intent": intent, **extra}


def get_api_context(question: str, intent: str) -> tuple[str, list[dict]]:

    # ── document lookups (no INN needed) ──────────────────────────────────────
    if intent == "get_document_types":
        data = get_document_types()
        ctx = format_json_context(data, title="Типы документов Faktura")
        return ctx, [_make_source("GetDocumentTypes", intent)]

    if intent == "get_document_creation_types":
        data = get_document_creation_types()
        ctx = format_json_context(data, title="Типы создания документов Faktura")
        return ctx, [_make_source("GetDocumentCreationTypes", intent)]

    if intent == "get_document_statuses":
        data = get_document_statuses()
        ctx = format_json_context(data, title="Статусы документов Faktura")
        return ctx, [_make_source("GetDocumentStatuses", intent)]

    if intent == "get_measurements":
        data = get_measurements()
        ctx = format_json_context(data, title="Единицы измерения Faktura")
        return ctx, [_make_source("GetMeasurements", intent)]

    # ── product catalog search ─────────────────────────────────────────────────
    if intent == "search_product_catalog":
        # pull search term: everything after "товар"/"икпу"/"ikpu" etc.
        q = question.strip()
        search_text = re.sub(
            r"(найди|найти|поиск|икпу|ikpu|каталог товаров|товар|код товара)\s*",
            "", q, flags=re.IGNORECASE
        ).strip() or q
        if len(search_text) < 2:
            ctx = ("Уточни что именно искать в каталоге товаров — "
                   "напиши название товара или ИКПУ код.")
            return ctx, [_make_source("ProductCatalogs/Search", intent)]
        data = search_product_catalog(search_text)
        ctx = format_json_context(data, title=f"Каталог товаров: поиск '{search_text}'")
        return ctx, [_make_source(f"ProductCatalogs/Search?{search_text}", intent)]

    # ── INN-based lookups ──────────────────────────────────────────────────────
    inn = extract_inn(question)

    if intent == "check_company_exists":
        if not inn:
            return _no_inn_context()
        data = check_company_exists(inn)
        ctx = f"""SOURCE: Faktura API — CheckCompanyExist/{inn}

ИНН: {inn}
РЕЗУЛЬТАТ: {data}

ПРАВИЛО ИНТЕРПРЕТАЦИИ:
- true  → компания с ИНН {inn} зарегистрирована в Faktura.uz
- false → компания не найдена / не зарегистрирована
- объект JSON → объясни поля простым языком"""
        return ctx, [_make_source(f"CheckCompanyExist/{inn}", intent, inn=inn)]

    if intent == "get_company_details":
        if not inn:
            return _no_inn_context("Нужны полные данные об организации. ")
        data = get_company_details(inn)
        ctx = format_json_context(
            data,
            title=f"Данные организации (ИНН {inn})",
            extra_hint="Объясни все поля пользователю: название, адрес, директор, ОКТМО и т.д."
        )
        return ctx, [_make_source(f"GetCompanyBasicDetails/{inn}", intent, inn=inn)]

    if intent == "check_nds_payer":
        if not inn:
            return _no_inn_context("Нужна проверка на плательщика НДС. ")
        data = check_nds_payer(inn)
        ctx = f"""SOURCE: Faktura API — IsNdsPayer/{inn}

ИНН: {inn}
РЕЗУЛЬТАТ: {data}

ПРАВИЛО ИНТЕРПРЕТАЦИИ:
- true  → компания {inn} является плательщиком НДС
- false → компания не является плательщиком НДС"""
        return ctx, [_make_source(f"IsNdsPayer/{inn}", intent, inn=inn)]

    if intent == "get_nds_vat_code":
        if not inn:
            return _no_inn_context("Нужен НДС/VAT код организации. ")
        data = get_nds_vat_code(inn)
        ctx = f"""SOURCE: Faktura API — GetNdsVatCode/{inn}

ИНН: {inn}
НДС КОД: {data}"""
        return ctx, [_make_source(f"GetNdsVatCode/{inn}", intent, inn=inn)]

    if intent == "get_company_branches":
        if not inn:
            return _no_inn_context("Нужен список филиалов компании. ")
        data = get_company_branches(inn)
        ctx = format_json_context(
            data,
            title=f"Филиалы организации (ИНН {inn})",
            extra_hint="branch_code — не ИНН, а внутренний код филиала из ГНИ."
        )
        return ctx, [_make_source(f"GetCompanyBranches/{inn}", intent, inn=inn)]

    if intent == "get_employees":
        data = get_employees(inn or "")
        ctx = format_json_context(data, title=f"Сотрудники организации{' ИНН ' + inn if inn else ''}")
        return ctx, [_make_source("GetEmployees", intent, inn=inn or "")]

    if intent == "get_company_roles":
        if not inn:
            return _no_inn_context("Нужен список ролей компании. ")
        data = get_company_roles(inn)
        ctx = format_json_context(data, title=f"Роли в организации (ИНН {inn})")
        return ctx, [_make_source(f"GetCompanyRoles/{inn}", intent, inn=inn)]

    if intent == "check_document_sync":
        return _check_document_sync(question)

    return "", []


# ── Document synchronisation check ─────────────────────────────────────────────

def _check_document_sync(question: str) -> tuple[str, list[dict]]:
    """
    Check whether a document's status in Faktura matches Soliq.

    Requires both INN (9 digits) and document UID (32-char hex) in the message.
    If either is missing, returns a prompt asking for the missing info.
    """
    inn = extract_inn(question)
    uid = extract_uid(question)

    # ── missing parameters ────────────────────────────────────────────────────
    if not inn and not uid:
        ctx = (
            "Пользователь хочет проверить синхронизацию документа с Солик, "
            "но ни ИНН, ни UID документа в сообщении не найдены.\n"
            "Попроси пользователя отправить:\n"
            "1. ИНН компании (9 цифр)\n"
            "2. UID документа (32-значный код, например: b357501454374cf0a6d1a840b8c4debb)"
        )
        return ctx, [_make_source("CheckDocumentSync", "check_document_sync")]

    if not inn:
        ctx = (
            f"Найден UID документа: {uid}.\n"
            "Но ИНН компании не указан.\n"
            "Попроси пользователя добавить 9-значный ИНН компании-владельца документа."
        )
        return ctx, [_make_source("CheckDocumentSync", "check_document_sync", uid=uid)]

    if not uid:
        ctx = (
            f"Найден ИНН: {inn}.\n"
            "Но UID документа не указан.\n"
            "Попроси пользователя добавить 32-значный UID документа "
            "(можно найти в Faktura.uz → открыть документ → скопировать из URL или карточки документа)."
        )
        return ctx, [_make_source("CheckDocumentSync", "check_document_sync", inn=inn)]

    log.info(f"🔄 Проверка синхронизации: ИНН={inn}, UID={uid}")

    # ── fetch from Faktura API ────────────────────────────────────────────────
    status_data = None
    details_data = None
    status_error = None
    details_error = None

    try:
        status_data = get_document_status(inn, uid)
    except Exception as e:
        status_error = str(e)
        log.warning(f"GetDocumentStatus error: {e}")

    try:
        details_data = get_document_details(inn, uid)
    except Exception as e:
        details_error = str(e)
        log.warning(f"GetDocumentDetails error: {e}")

    # both failed — can't check
    if status_data is None and details_data is None:
        ctx = (
            f"ИНН: {inn}\nUID: {uid}\n\n"
            f"Не удалось получить данные из Faktura API.\n"
            f"Ошибка статуса: {status_error}\n"
            f"Ошибка деталей: {details_error}\n\n"
            "Сообщи пользователю об ошибке и предложи обратиться в поддержку."
        )
        return ctx, [_make_source(f"CheckDocumentSync/{inn}/{uid}", "check_document_sync", inn=inn, uid=uid)]

    # ── analyse statuses ──────────────────────────────────────────────────────
    faktura_status, soliq_status, mismatch = _extract_sync_statuses(status_data, details_data)

    # build context for Gemini
    sections = [
        f"ИНН компании: {inn}",
        f"UID документа: {uid}",
        "",
    ]

    if status_data is not None:
        sections.append("=== Статус из GetDocumentStatus ===")
        sections.append(json.dumps(status_data, ensure_ascii=False, indent=2))
        sections.append("")

    if details_data is not None:
        sections.append("=== Детали документа (GetDetails) ===")
        sections.append(json.dumps(details_data, ensure_ascii=False, indent=2))
        sections.append("")

    if faktura_status:
        sections.append(f"СТАТУС В FAKTURA: {faktura_status}")
    if soliq_status:
        sections.append(f"СТАТУС В СОЛИК: {soliq_status}")

    if mismatch:
        sections.append("")
        sections.append("⚠️ ОБНАРУЖЕНО РАСХОЖДЕНИЕ статусов между Faktura и Солик!")
        sections.append("Это критическая проблема. Требуется немедленная проверка администратором.")
        sections.append(
            "ИНСТРУКЦИЯ ДЛЯ ОТВЕТА:\n"
            "1. Сообщи пользователю что обнаружено расхождение статусов.\n"
            "2. Покажи статус Faktura и статус Солик отдельно.\n"
            "3. Скажи что проблема отмечена как КРИТИЧЕСКАЯ и передана администратору.\n"
            "4. Попроси пользователя подождать — администратор разберётся в ближайшее время."
        )
    else:
        sections.append("")
        sections.append(
            "ИНСТРУКЦИЯ ДЛЯ ОТВЕТА:\n"
            "Статусы совпадают или расхождений не обнаружено.\n"
            "Объясни пользователю текущий статус документа простым языком."
        )

    ctx = "\n".join(sections)

    # critical flag goes into source so bot_engine forces review
    source = _make_source(f"CheckDocumentSync/{inn}/{uid}", "check_document_sync",
                          inn=inn, uid=uid, is_critical=mismatch)

    return ctx, [source]


def _extract_sync_statuses(
    status_data: list | dict | None,
    details_data: dict | None,
) -> tuple[str, str, bool]:
    """
    Extract Faktura status and Soliq status from API responses.
    Returns (faktura_status_text, soliq_status_text, is_mismatch).
    """
    faktura_status = ""
    soliq_status = ""

    # ── from GetDocumentStatus response ──────────────────────────────────────
    if isinstance(status_data, list) and status_data:
        item = status_data[0]
        faktura_status = _read_status_field(item, [
            "statusName", "status_name", "status", "statusDescription",
            "facturaStatus", "faktura_status",
        ])
        soliq_status = _read_status_field(item, [
            "soliqStatus", "soliq_status", "soliqStatusName", "soliq_status_name",
            "taxStatus", "tax_status", "taxStatusName", "soliqStatusDescription",
        ])

    elif isinstance(status_data, dict):
        faktura_status = _read_status_field(status_data, [
            "statusName", "status", "facturaStatus",
        ])
        soliq_status = _read_status_field(status_data, [
            "soliqStatus", "soliqStatusName", "taxStatus",
        ])

    # ── supplement from GetDetails if not found yet ───────────────────────────
    if details_data and isinstance(details_data, dict):
        if not faktura_status:
            faktura_status = _read_status_field(details_data, [
                "statusName", "status", "facturaStatus", "faktura_status",
            ])
        if not soliq_status:
            soliq_status = _read_status_field(details_data, [
                "soliqStatus", "soliqStatusName", "taxStatus", "tax_status",
                "soliqStatusDescription", "soliq_status",
            ])

    # ── determine mismatch ────────────────────────────────────────────────────
    # mismatch only if BOTH are known and they differ
    mismatch = False
    if faktura_status and soliq_status:
        # normalise: strip whitespace, lowercase
        f_norm = str(faktura_status).strip().lower()
        s_norm = str(soliq_status).strip().lower()
        if f_norm != s_norm:
            mismatch = True

    return str(faktura_status), str(soliq_status), mismatch


def _read_status_field(obj: dict, field_names: list[str]) -> str:
    """Try multiple field name variants, return first non-empty value found."""
    for name in field_names:
        val = obj.get(name)
        if val is not None and str(val).strip():
            return str(val).strip()
    return ""
