
import json
from pathlib import Path
from datetime import datetime

from app.admin.services.admin_access import log_admin_action

BASE_DIR = Path(__file__).resolve().parents[3]

ADMIN_DATA_DIR = BASE_DIR / "data" / "admin"
READ_ONLY_SETTINGS_PATH = ADMIN_DATA_DIR / "read_only_settings.json"

READ_ONLY_MODES = {"all", "selected", "off"}

DEFAULT_SETTINGS = {
    "mode": "off",
    "chat_ids": [],
    "updated_at": "",
    "updated_by": "",
}

def ensure_settings_file() -> None:
    ADMIN_DATA_DIR.mkdir(parents=True, exist_ok=True)

    if READ_ONLY_SETTINGS_PATH.exists():
        return
    
    save_settings = save_settings(DEFAULT_SETTINGS.copy())

def normalize_chat_id(chat_id: int | str | None) -> str:
    if chat_id is None:
        return ""
    
    return str(chat_id).strip()

def normalize_chat_ids_list(value) -> list[str]:
    if value is None:
        return []
    
    if isinstance(value, list):
        return [
            normalize_chat_id(item)
            for item in value
            if normalize_chat_id(item)
        ]
    
    if isinstance(value, str):
        if not value.strip:
            return []
        
        return [
            normalize_chat_id(item)
            for item in value.split(",")
            if normalize_chat_id(item)
        ]
    
    return [
        normalize_chat_id(value)
    ]

def load_settings() -> dict:
    ensure_settings_file()

    try:
        with open(READ_ONLY_SETTINGS_PATH, mode="r", encoding="utf-8-sig") as f:
            data = json.load(f)

        if not isinstance(data, dict):
            return DEFAULT_SETTINGS.copy()
        
        settings = DEFAULT_SETTINGS.copy()
        settings.update(data)

        if settings.get("mode") not in READ_ONLY_MODES:
            settings["mode"] = "off"

        if not isinstance(settings.get("chat_ids"), list):
            settings["chat_ids"] = []

        settings["chat_ids"] = [
            normalize_chat_id(chat_id)
            for chat_id in settings["chat_ids"]
            if normalize_chat_id(chat_id)
        ]

        return settings
    
    except Exception:
        return DEFAULT_SETTINGS.copy()
    

def save_settings(settings: dict) -> None:
    ADMIN_DATA_DIR.mkdir(parents=True, exist_ok=True)

    with open(READ_ONLY_SETTINGS_PATH, mode="w", encoding="utf-8-sig") as f:
        json.dump(settings, f, ensure_ascii=False,indent=2, )


def get_read_only_mode() -> str:
    settings = load_settings()
    return settings.get("mode", "off")


def set_read_only_mode(
        mode: str,
        admin_id: int | None = None,
)-> bool:
    if mode not in READ_ONLY_MODES:
        return False
    
    settings = load_settings()
    settings["mode"] = mode
    settings["updated_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    settings["updated_by"] = str(admin_id or "")

    save_settings(settings)

    log_admin_action(
        admin_id=admin_id,
        action="set_read_only_mode",
        details=mode,
    )

    return True


def get_read_only_chat_ids() -> list[str]:
    settings = load_settings()
    return normalize_chat_ids_list(settings.get("chat_ids", []))


def add_read_only_chat(
        chat_id: int | str,
        admin_id: int | None = None,
)-> bool:
    chat_id_str = normalize_chat_id(chat_id)

    if not chat_id_str:
        return False
    
    settings = load_settings()

    current_chat_ids = normalize_chat_ids_list(
        settings.get("chat_ids", [])
    )

    new_chat_ids = list(
        dict.fromkeys(
            current_chat_ids + [chat_id_str]
        )
    )

    settings["chat_ids"] = new_chat_ids
    settings["updated_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    settings["updated_by"] = str(admin_id or "")

    save_settings(settings)

    log_admin_action(
        admin_id=admin_id,
        action="add_read_only_chat",
        details=chat_id_str,
    )

    return True


def remove_read_only_chat(
        chat_id: int | str,
        admin_id: int | None = None,
)-> bool:
    chat_id_str = normalize_chat_id(chat_id)

    if not chat_id_str:
        return False
    
    settings = load_settings()

    current_chat_ids = normalize_chat_ids_list(
        settings.get("chat_ids", [])
    )

    if chat_id_str not in current_chat_ids:
        return False
    
    new_chat_ids = [
        existing_chat_id
        for existing_chat_id in current_chat_ids
        if existing_chat_id != chat_id_str
    ]
    

    settings["chat_ids"] = new_chat_ids
    settings["updated_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    settings["updated_by"] = str(admin_id or "")

    save_settings(settings)

    log_admin_action(
        admin_id=admin_id,
        action="remove_read_only_chat",
        details=chat_id_str,
    )

    return True


def is_read_only_for_chat(chat_id: int | str) -> bool:
    settings = load_settings()
    mode = settings.get("mode", "off")

    if mode == "off":
        return False
    
    if mode == "all":
        return True
    
    if mode == "selected":
        chat_id_str = normalize_chat_id(chat_id)
        chat_ids = normalize_chat_ids_list(settings.get("chat_ids", []))
        return chat_id_str in chat_ids
    
    return False

def format_read_only_status(language: str= "ru") -> str:
    settings = load_settings()
    mode = settings.get("mode", "off")
    chat_ids = settings.get("chat_ids", [])
    updated_at = settings.get("updated_at", "")
    updated_by = settings.get("updated_by", "")

    if mode == "all":
        mode_text = "везде"
    elif mode == "selected":
        mode_text = "в выбранных чатах"
    else:
        mode_text = "отключён"

    chats_text = "\n".join(f"- {chat_id}" for chat_id in chat_ids)

    if not chats_text:
        chats_text = "список пуст"

    return (
        "🔐 Read-only режим\n\n"
        f"Текущий режим: {mode_text}\n"
        f"Выбранные чаты:\n{chats_text}\n\n"
        f"Обновлено: {updated_at or 'нет данных'}\n"
        f"Кем обновлено: {updated_by or 'нет данных'}"
    )

