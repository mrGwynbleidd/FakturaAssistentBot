# admin panel handler for read-only (group monitoring) mode
# shows list of monitored groups with their titles and current mode
# adding/removing groups is done via /readonly command in the group itself
# used in admin_router.py

from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message

from app.admin.services.admin_access import is_admin, get_admin_language
from app.admin.services.read_only_service import (
    set_read_only_mode,
    format_read_only_status,
)
from app.admin.texts import get_admin_text
from app.admin.keyboards.read_only import read_only_keyboard

router = Router(name="admin_read_only")


# returns all localized button texts + known aliases for safe filter matching
def _btn(key: str) -> list[str]:
    values = [get_admin_text(key, lang) for lang in ("ru", "uz", "en")]
    aliases = {
        "btn_read_only": ["🔐 Read-only режим", "readonly", "read_only"],
        "btn_read_only_all": ["1️⃣ Read-only везде", "all"],
        "btn_read_only_selected": ["2️⃣ Read-only в выбранных чатах", "selected"],
        "btn_read_only_off": ["3️⃣ Выключить сбор", "3️⃣ Read-only отключить", "off"],
        # legacy buttons from old keyboard — redirect to the status panel
        "btn_read_only_list_chats": ["📋 Список read-only чатов", "list_read_only_chats"],
        "btn_read_only_add_current_chat": ["➕ Добавить текущий чат", "add_current_chat"],
        "btn_read_only_remove_current_chat": ["➖ Удалить текущий чат", "remove_current_chat"],
    }
    values.extend(aliases.get(key, []))
    return list(set(values))


# sends the read-only status panel to admin
async def _send_menu(message: Message) -> None:
    if not is_admin(message.from_user.id if message.from_user else None):
        await message.answer(get_admin_text("access_denied", "ru"))
        return
    language = get_admin_language(message.from_user.id if message.from_user else None)
    await message.answer(
        format_read_only_status(language),
        reply_markup=read_only_keyboard(language),
    )


# opens read-only panel from main menu button or /readonly command in private chat
# also handles legacy cached buttons (list, add, remove) — they all just show the panel
@router.message(Command("readonly"))
@router.message(F.text.in_(_btn("btn_read_only")))
@router.message(F.text.in_(_btn("btn_read_only_list_chats")))
@router.message(F.text.in_(_btn("btn_read_only_add_current_chat")))
@router.message(F.text.in_(_btn("btn_read_only_remove_current_chat")))
async def read_only_menu(message: Message) -> None:
    await _send_menu(message)


# mode: collect from ALL groups
@router.message(F.text.in_(_btn("btn_read_only_all")))
async def read_only_all(message: Message) -> None:
    if not is_admin(message.from_user.id if message.from_user else None):
        return
    admin_id = message.from_user.id if message.from_user else None
    language = get_admin_language(admin_id)
    set_read_only_mode("all", admin_id=admin_id)
    await message.answer(
        get_admin_text("readonly_enabled_all", language),
        reply_markup=read_only_keyboard(language),
    )


# mode: collect only from chats registered with /readonly
@router.message(F.text.in_(_btn("btn_read_only_selected")))
async def read_only_selected(message: Message) -> None:
    if not is_admin(message.from_user.id if message.from_user else None):
        return
    admin_id = message.from_user.id if message.from_user else None
    language = get_admin_language(admin_id)
    set_read_only_mode("selected", admin_id=admin_id)
    await message.answer(
        get_admin_text("readonly_enabled_selected", language),
        reply_markup=read_only_keyboard(language),
    )


# mode: off — stop collecting from all groups
@router.message(F.text.in_(_btn("btn_read_only_off")))
async def read_only_off(message: Message) -> None:
    if not is_admin(message.from_user.id if message.from_user else None):
        return
    admin_id = message.from_user.id if message.from_user else None
    language = get_admin_language(admin_id)
    set_read_only_mode("off", admin_id=admin_id)
    await message.answer(
        get_admin_text("readonly_disabled", language),
        reply_markup=read_only_keyboard(language),
    )
