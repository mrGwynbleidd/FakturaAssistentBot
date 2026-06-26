import csv
import json
import os
import re

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

BASE_DIR = Path(__file__).resolve().parents[2]
LOGS_DIR = BASE_DIR / "data" / "logs"
SYNC_LOG_PATH = LOGS_DIR / "sync_roaming_requests.csv"

FAKTURA_API_BASE_URL = os.getenv(
    "FAKTURA_API_BASE_URL", "https://api.faktura.uz"
).rstrip("/")

SYNC_ROAMING_TIMEOUT_SECONDS = int(os.getenv("SYNC_ROAMING_TIMEOUT_SECONDS", "35"))

MODEL_TYPES: dict[int, str] = {
    0: "Счет фактура",
    1: "Доверенность",
    2: "Акт",
    3: "Накладной",
    4: "Акт сверки",
    5: "Договор",
}

CONTRACTOR_TYPES: dict[int, str] = {
    0: "Отправитель",
    1: "Получатель",
}

SYNC_LOG_FIELDNAMES = [
    "datetime", "user_id", "username", "chat_id", "chat_title",
    "roaming_id", "inn", "model_type", "model_name",
    "contractor_type_used", "http_status", "ok", "error",
]


@dataclass
class SyncRoamingResult:
    contractor_type: int
    contractor_name: str
    ok: bool
    status_code: int | None
    url: str
    response_json: Any
    response_text: str
    error: str = ""


# ── Validation ────────────────────────────────────────────────────────────────

# roaming id is a MongoDB ObjectId — exactly 24 lowercase hex characters
def validate_roaming_id(roaming_id: str) -> str:
    roaming_id = str(roaming_id or "").strip()
    if not roaming_id:
        raise ValueError("Roaming ID не указан.")
    if not re.fullmatch(r"[a-fA-F0-9]{24}", roaming_id):
        raise ValueError(
            f"Неверный Roaming ID: получено {len(roaming_id)} символов.\n"
            "Roaming ID должен содержать ровно 24 шестнадцатеричных символа.\n"
            "Пример: `691c6a9e2456ead059405099`"
        )
    return roaming_id.lower()


# accepts 9-digit INN (company) or 16-digit PINFL (individual)
def validate_inn(inn: str) -> str:
    inn = str(inn or "").strip()
    if not inn.isdigit():
        raise ValueError("ИНН / ПИНФЛ должен содержать только цифры.")
    if len(inn) == 9:
        return inn
    if len(inn) == 14:
        return inn
    raise ValueError(
        f"Неверная длина: получено {len(inn)} цифр.\n"
        "ИНН юрлица — 9 цифр, ПИНФЛ физлица — 14 цифр.\n"
        "Примеры: `205126427` или `12345678901234`"
    )


def validate_model_type(model_type: int | str) -> int:
    try:
        v = int(str(model_type).strip())
    except ValueError:
        raise ValueError("Тип документа должен быть числом от 0 до 5")
    if v not in MODEL_TYPES:
        raise ValueError("Неверный тип документа. Доступно 0–5")
    return v


def parse_model_type_from_text(text: str | None) -> int:
    text = str(text or "").strip()

    # "Счет фактура = 0" — from keyboard button
    match = re.search(r"=\s*([0-5])\s*$", text)
    if match:
        return validate_model_type(match.group(1))

    # bare digit
    if text in {"0", "1", "2", "3", "4", "5"}:
        return validate_model_type(text)

    lowered = text.lower()
    for model_type, title in MODEL_TYPES.items():
        if title.lower() in lowered:
            return model_type

    aliases = {
        "счет-фактура": 0, "счёт-фактура": 0,
        "invoice": 0, "доверенность": 1, "акт сверки": 4,
        "акт": 2, "накладная": 3, "накладной": 3, "ттн": 3, "договор": 5,
    }
    for alias, mt in aliases.items():
        if alias in lowered:
            return mt

    return validate_model_type(text)



def _sync_one_contractor_type_sync(
    roaming_id: str, inn: str, model_type: int, contractor_type: int,
) -> SyncRoamingResult:
    """Synchronous inner call — runs in a thread via asyncio.to_thread."""
    from app.faktura_api.client import build_headers
    import requests

    endpoint = f"/Api/Patch/SyncRoamingDocument/{roaming_id}"
    url = f"{FAKTURA_API_BASE_URL.rstrip('/')}/{endpoint.lstrip('/')}"
    params = {"inn": inn, "contractorType": contractor_type, "modelType": model_type}

    try:
        resp = requests.get(
            url,
            headers=build_headers(),
            params=params,
            timeout=SYNC_ROAMING_TIMEOUT_SECONDS,
        )
        try:
            response_json = resp.json()
        except Exception:
            response_json = None
        return SyncRoamingResult(
            contractor_type=contractor_type,
            contractor_name=CONTRACTOR_TYPES[contractor_type],
            ok=200 <= resp.status_code < 300,
            status_code=resp.status_code,
            url=resp.url,
            response_json=response_json,
            response_text=resp.text,
        )
    except Exception as exc:
        return SyncRoamingResult(
            contractor_type=contractor_type,
            contractor_name=CONTRACTOR_TYPES[contractor_type],
            ok=False,
            status_code=None,
            url=url,
            response_json=None,
            response_text="",
            error=str(exc),
        )


async def sync_one_contractor_type(
    roaming_id: str, inn: str, model_type: int, contractor_type: int,
) -> SyncRoamingResult:
    import asyncio
    return await asyncio.to_thread(
        _sync_one_contractor_type_sync, roaming_id, inn, model_type, contractor_type
    )


async def sync_roaming_document(
    roaming_id: str, inn: str, model_type: int,
) -> SyncRoamingResult:
    """Try contractorType=0 first; on error try contractorType=1."""
    roaming_id = validate_roaming_id(roaming_id)
    inn = validate_inn(inn)
    model_type = validate_model_type(model_type)

    for contractor_type in (0, 1):
        result = await sync_one_contractor_type(roaming_id, inn, model_type, contractor_type)
        if result.ok:
            return result

    # both failed — return the last result (contractorType=1) with error context
    return result


# ── Formatting (direct, no AI) ────────────────────────────────────────────────

def _get(data: Any, *keys: str) -> str:
    """Case-insensitive deep search for a key in nested dict/list."""
    if data is None:
        return ""
    lower_keys = {k.lower() for k in keys}
    if isinstance(data, dict):
        for k, v in data.items():
            if k.lower() in lower_keys:
                return str(v) if v is not None else ""
        for v in data.values():
            found = _get(v, *keys)
            if found:
                return found
    if isinstance(data, list):
        for item in data:
            found = _get(item, *keys)
            if found:
                return found
    return ""


def format_sync_result(model_type: int, result: SyncRoamingResult) -> str:
    model_name = MODEL_TYPES.get(model_type, str(model_type))

    if not result.ok:
        reason = result.error or f"HTTP {result.status_code}"
        # Give contractor_type context in the error
        tried = "Отправитель и Получатель"
        return (
            f"❌ Не удалось синхронизировать документ.\n"
            f"Проверены: {tried}\n"
            f"Причина: {reason}"
        )

    d = result.response_json or {}
    uid             = _get(d, "uniqueId", "uid", "id")
    sender_inn      = _get(d, "otpravitelInn", "senderInn", "fromInn")
    sender_status   = _get(d, "otpravitelStatus", "senderStatus", "fromStatus")
    receiver_inn    = _get(d, "poluchatelInn", "receiverInn", "toInn")
    receiver_status = _get(d, "poluchatelStatus", "receiverStatus", "toStatus")
    roaming_status  = _get(d, "roamingStatus", "status", "syncStatus")

    lines = [f"✅ Документ {model_name} синхронизирован"]
    lines.append("")
    if uid:
        lines.append(f"🔑 UID: {uid}")
    if sender_inn or sender_status:
        lines.append(f"📤 Отправитель: {sender_inn} в состоянии {sender_status}")
    if receiver_inn or receiver_status:
        lines.append(f"📥 Получатель: {receiver_inn} в состоянии {receiver_status}")
    if roaming_status:
        lines.append(f"📋 Статус документа: {roaming_status}")

    # If response didn't have the expected fields, show the raw JSON briefly
    if not any([uid, sender_inn, receiver_inn, roaming_status]):
        raw = json.dumps(d, ensure_ascii=False, indent=2)
        if len(raw) > 1200:
            raw = raw[:1200] + "\n..."
        lines.append(f"\nОтвет API:\n{raw}")

    #lines.append(f"\n(contractorType={result.contractor_type} — {result.contractor_name})")
    return "\n".join(lines)


# ── Logging ───────────────────────────────────────────────────────────────────

def _ensure_sync_log() -> None:
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    if not SYNC_LOG_PATH.exists():
        with open(SYNC_LOG_PATH, "w", encoding="utf-8-sig", newline="") as f:
            csv.DictWriter(f, fieldnames=SYNC_LOG_FIELDNAMES).writeheader()


def log_sync_request(
    user_id: int | str | None,
    username: str | None,
    chat_id: int | str | None,
    chat_title: str | None,
    roaming_id: str,
    inn: str,
    model_type: int,
    result: SyncRoamingResult,
) -> None:
    _ensure_sync_log()
    row = {
        "datetime": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "user_id": str(user_id or ""),
        "username": str(username or ""),
        "chat_id": str(chat_id or ""),
        "chat_title": str(chat_title or ""),
        "roaming_id": roaming_id,
        "inn": inn,
        "model_type": str(model_type),
        "model_name": MODEL_TYPES.get(model_type, ""),
        "contractor_type_used": str(result.contractor_type),
        "http_status": str(result.status_code or ""),
        "ok": str(result.ok),
        "error": result.error,
    }
    with open(SYNC_LOG_PATH, "a", encoding="utf-8-sig", newline="") as f:
        csv.DictWriter(f, fieldnames=SYNC_LOG_FIELDNAMES).writerow(row)
