# manages read-only (monitored) group chat settings
# read-only = bot silently collects messages from the group without responding
# chats are registered via /readonly command in the group chat itself
# used by group_handlers.py (gate) and admin read_only handler (panel view)

import json
import logging
from pathlib import Path
from datetime import datetime

from app.admin.services.admin_access import log_admin_action

log = logging.getLogger("bot")

BASE_DIR = Path(__file__).resolve().parents[3]
ADMIN_DATA_DIR = BASE_DIR / "data" / "admin"
READ_ONLY_SETTINGS_PATH = ADMIN_DATA_DIR / "read_only_settings.json"

# mode values:
#   "off"      — bot does not collect from any group
#   "selected" — bot collects only from groups in the chats dict
#   "all"      — bot collects from every group it is in
READ_ONLY_MODES = {"all", "selected", "off"}

DEFAULT_SETTINGS: dict = {
    "mode": "selected",
    "chats": {},       # {chat_id_str: {title, username, added_at, added_by}}
    "updated_at": "",
    "updated_by": "",
}


# ── internal helpers ───────────────────────────────────────────────────────────

def _normalize_id(chat_id) -> str:
    if chat_id is None:
        return ""
    return str(chat_id).strip()


def _write(settings: dict) -> None:
    ADMIN_DATA_DIR.mkdir(parents=True, exist_ok=True)
    with open(READ_ONLY_SETTINGS_PATH, mode="w", encoding="utf-8-sig") as f:
        json.dump(settings, f, ensure_ascii=False, indent=2)


def _ensure_file() -> None:
    ADMIN_DATA_DIR.mkdir(parents=True, exist_ok=True)
    if not READ_ONLY_SETTINGS_PATH.exists():
        _write(DEFAULT_SETTINGS.copy())


# ── public: load / save ────────────────────────────────────────────────────────

# reads settings from json, falls back to defaults on any error
# returns dict with validated mode and chats fields
def load_settings() -> dict:
    _ensure_file()
    try:
        with open(READ_ONLY_SETTINGS_PATH, encoding="utf-8-sig") as f:
            data = json.load(f)
        if not isinstance(data, dict):
            return DEFAULT_SETTINGS.copy()

        settings = DEFAULT_SETTINGS.copy()
        settings.update(data)

        # validate mode
        if settings.get("mode") not in READ_ONLY_MODES:
            settings["mode"] = "selected"

        # migrate old format: "chat_ids" list → "chats" dict
        if "chat_ids" in settings and "chats" not in settings:
            chats = {}
            for cid in settings.pop("chat_ids", []):
                cid_str = _normalize_id(cid)
                if cid_str:
                    chats[cid_str] = {"title": cid_str, "username": "", "added_at": "", "added_by": ""}
            settings["chats"] = chats
        elif not isinstance(settings.get("chats"), dict):
            settings["chats"] = {}

        return settings
    except Exception:
        return DEFAULT_SETTINGS.copy()


# ── public: mode ───────────────────────────────────────────────────────────────

# returns current mode string ("all", "selected", "off")
def get_mode() -> str:
    return load_settings().get("mode", "selected")


# sets global read-only mode, returns False on invalid mode value
# called from admin panel mode buttons
def set_read_only_mode(mode: str, admin_id=None) -> bool:
    if mode not in READ_ONLY_MODES:
        return False
    settings = load_settings()
    settings["mode"] = mode
    settings["updated_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    settings["updated_by"] = str(admin_id or "")
    _write(settings)
    log_admin_action(admin_id=admin_id, action="set_read_only_mode", details=mode)
    return True


# ── public: chat list ──────────────────────────────────────────────────────────

# returns dict of all registered chats: {chat_id_str: {title, username, added_at, added_by}}
def get_chats() -> dict:
    return load_settings().get("chats", {})


# adds a chat to the monitored list with its title and optional username
# called from group /readonly command handler — stores real group name
# returns False if chat_id is empty
def add_read_only_chat(chat_id, title: str = "", username: str = "", admin_id=None) -> bool:
    chat_id_str = _normalize_id(chat_id)
    if not chat_id_str:
        return False

    settings = load_settings()
    settings["chats"][chat_id_str] = {
        "title": title or chat_id_str,
        "username": username or "",
        "added_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "added_by": str(admin_id or ""),
    }
    settings["updated_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    settings["updated_by"] = str(admin_id or "")
    _write(settings)
    log_admin_action(admin_id=admin_id, action="add_read_only_chat", details=f"{chat_id_str} ({title})")
    return True


# removes a chat from the monitored list
# returns False if not found
def remove_read_only_chat(chat_id, admin_id=None) -> bool:
    chat_id_str = _normalize_id(chat_id)
    if not chat_id_str:
        return False

    settings = load_settings()
    if chat_id_str not in settings.get("chats", {}):
        return False

    del settings["chats"][chat_id_str]
    settings["updated_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    settings["updated_by"] = str(admin_id or "")
    _write(settings)
    log_admin_action(admin_id=admin_id, action="remove_read_only_chat", details=chat_id_str)
    return True


# ── public: gate check ─────────────────────────────────────────────────────────

# returns True if the bot should collect (silently observe) this chat
# "off"      → False (collect nothing)
# "all"      → True  (collect from all groups)
# "selected" → True only if chat_id is in the registered list
# used at the top of every group handler to gate message processing
def is_collecting_for_chat(chat_id) -> bool:
    settings = load_settings()
    mode = settings.get("mode", "selected")

    if mode == "off":
        return False
    if mode == "all":
        return True
    if mode == "selected":
        return _normalize_id(chat_id) in settings.get("chats", {})
    return False


# ── public: formatting ─────────────────────────────────────────────────────────

# formats current status as readable text for admin panel
# shows mode, list of monitored chats with titles, last update info
def format_read_only_status(language: str = "ru") -> str:
    settings = load_settings()
    mode = settings.get("mode", "selected")
    chats: dict = settings.get("chats", {})
    updated_at = settings.get("updated_at", "")
    updated_by = settings.get("updated_by", "")

    mode_labels = {
        "all": "все группы",
        "selected": "выбранные группы",
        "off": "отключён",
    }
    mode_text = mode_labels.get(mode, mode)

    if chats:
        chat_lines = []
        for cid, meta in chats.items():
            title = meta.get("title") or cid
            uname = meta.get("username", "")
            added = meta.get("added_at", "")
            line = f"• {title}"
            if uname:
                line += f" (@{uname})"
            line += f"\n  ID: {cid}"
            if added:
                line += f"  |  добавлен: {added}"
            chat_lines.append(line)
        chats_text = "\n".join(chat_lines)
    else:
        chats_text = "  список пуст"

    lines = [
        "🔐 Read-only режим (сбор сообщений из групп)",
        "",
        f"Режим: {mode_text}",
        "",
        "Отслеживаемые чаты:",
        chats_text,
        "",
        "ℹ️ Чтобы добавить группу — отправь /readonly в ту группу.",
    ]
    if updated_at:
        lines.append(f"\nОбновлено: {updated_at}  |  кем: {updated_by or '—'}")

    return "\n".join(lines)
