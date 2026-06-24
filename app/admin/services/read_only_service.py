#manages read-only mode settings stored in read_only_settings.json
#read-only mode prevents the bot from answering in selected or all chats
#used in read_only handler and read_only_middleware

import json
from pathlib import Path
from datetime import datetime

from app.admin.services.admin_access import log_admin_action

BASE_DIR = Path(__file__).resolve().parents[3]

ADMIN_DATA_DIR = BASE_DIR / "data" / "admin"
READ_ONLY_SETTINGS_PATH = ADMIN_DATA_DIR / "read_only_settings.json"

#valid mode values: all = block everywhere, selected = block specific chats, off = disabled
READ_ONLY_MODES = {"all", "selected", "off"}

#default settings when no file exists
DEFAULT_SETTINGS = {
    "mode": "off",
    "chat_ids": [],
    "updated_at": "",
    "updated_by": "",
}

#creates the settings file with default values if it does not exist
def ensure_settings_file() -> None:
    ADMIN_DATA_DIR.mkdir(parents=True, exist_ok=True)

    if READ_ONLY_SETTINGS_PATH.exists():
        return
    
    save_settings = save_settings(DEFAULT_SETTINGS.copy())

#normalizes a chat_id to a string, returns empty string if None
def normalize_chat_id(chat_id: int | str | None) -> str:
    if chat_id is None:
        return ""
    
    return str(chat_id).strip()

#converts a chat_ids value of any type (list, str, single value) to a normalized list of strings
#used when loading and saving chat_ids in settings
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

#reads settings from json file, falls back to defaults on any error
#validates mode and chat_ids fields before returning
#used by all read-only service functions
def load_settings() -> dict:
    ensure_settings_file()

    try:
        with open(READ_ONLY_SETTINGS_PATH, mode="r", encoding="utf-8-sig") as f:
            data = json.load(f)

        if not isinstance(data, dict):
            return DEFAULT_SETTINGS.copy()
        
        settings = DEFAULT_SETTINGS.copy()
        settings.update(data)

        #reset invalid mode to off
        if settings.get("mode") not in READ_ONLY_MODES:
            settings["mode"] = "off"

        #ensure chat_ids is always a list
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
    

#writes settings dict to json file
#used by set_read_only_mode, add_read_only_chat, and remove_read_only_chat
def save_settings(settings: dict) -> None:
    ADMIN_DATA_DIR.mkdir(parents=True, exist_ok=True)

    with open(READ_ONLY_SETTINGS_PATH, mode="w", encoding="utf-8-sig") as f:
        json.dump(settings, f, ensure_ascii=False,indent=2, )


#returns the current read-only mode string ("all", "selected", or "off")
#used in is_read_only_for_chat
def get_read_only_mode() -> str:
    settings = load_settings()
    return settings.get("mode", "off")


#sets the global read-only mode, saves settings, logs the action
#returns False if mode value is invalid
#used in read_only handler buttons
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


#returns the normalized list of chat ids currently in the read-only list
#used in is_read_only_for_chat and format_read_only_status
def get_read_only_chat_ids() -> list[str]:
    settings = load_settings()
    return normalize_chat_ids_list(settings.get("chat_ids", []))


#adds a chat_id to the read-only list, deduplicates, saves, and logs
#returns False if chat_id is empty
#used in read_only handler add button
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

    #deduplicate while preserving order
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


#removes a chat_id from the read-only list, saves, and logs
#returns False if chat_id is empty or not in the list
#used in read_only handler remove button
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


#returns True if the given chat is currently blocked by read-only mode
#used in read_only_middleware to decide whether to process a message
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

#formats current read-only settings as a human-readable status text
#used in send_read_only_menu to display current state to admin
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
