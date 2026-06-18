
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message

from app.admin.services.admin_access import is_admin, get_admin_language
from app.admin.services.read_only_service import (
    set_read_only_mode,
    add_read_only_chat,
    remove_read_only_chat,
    format_read_only_status,
)
from app.admin.texts import get_admin_text
from app.admin.keyboards.read_only import read_only_keyboard

router = Router(name="admin_read_only")

def text_values(key: str) -> list[str]:
    values = [
        get_admin_text(key, "ru"),
        get_admin_text(key, "uz"),
        get_admin_text(key, "en"),
        key,
    ]

    aliases = {
        "btn_read_only": [
            "readonly",
            "read_only",
            "btn_read_only",
            "🔐 Read-only режим",
        ],
        "btn_read_only_all": [
            "1",
            "all",
            "read_only_all",
            "1️⃣ Read-only везде",
        ],
        "btn_read_only_selected": [
            "2",
            "selected",
            "read_only_selected",
            "2️⃣ Read-only в выбранных чатах",
        ],
        "btn_read_only_off": [
            "3",
            "off",
            "read_only_off",
            "3️⃣ Read-only отключить",
        ],
        "btn_read_only_add_current_chat": [
            "add_current_chat",
            "➕ Добавить текущий чат",
        ],
        "btn_read_only_remove_current_chat": [
            "remove_current_chat",
            "➖ Удалить текущий чат",
        ],
        "btn_read_only_list_chats": [
            "list_read_only_chats",
            "📋 Список read-only чатов",
        ],
    }

    values.extend(aliases.get(key, []))

    return list(set(values))


async def send_read_only_menu(message: Message) -> None:
    if not is_admin(message.from_user.id if message.from_user else None):
        await message.answer(get_admin_text("access_denied", "ru"))
        return

    language = get_admin_language(message.from_user.id if message.from_user else None)

    await message.answer(
        format_read_only_status(language),
        reply_markup=read_only_keyboard(language),
    )

@router.message(Command("readonly"))
@router.message(F.text.in_(text_values("btn_read_only")))
async def read_only_menu(message: Message):
    await send_read_only_menu(message)


@router.message(F.text.in_(text_values("btn_read_only_all")))
async def read_only_all(message: Message):
    if not is_admin(message.from_user.id if message.from_user else None):
        return

    admin_id = message.from_user.id if message.from_user else None
    language = get_admin_language(admin_id)

    set_read_only_mode("all", admin_id=admin_id)

    await message.answer(
        get_admin_text("readonly_enabled_all", language),
        reply_markup=read_only_keyboard(language),
    )


@router.message(F.text.in_(text_values("btn_read_only_selected")))
async def read_only_selected(message: Message):
    if not is_admin(message.from_user.id if message.from_user else None):
        return

    admin_id = message.from_user.id if message.from_user else None
    language = get_admin_language(admin_id)

    set_read_only_mode("selected", admin_id=admin_id)

    await message.answer(
        get_admin_text("readonly_enabled_selected", language),
        reply_markup=read_only_keyboard(language),
    )


@router.message(F.text.in_(text_values("btn_read_only_off")))
async def read_only_off(message: Message):
    if not is_admin(message.from_user.id if message.from_user else None):
        return

    admin_id = message.from_user.id if message.from_user else None
    language = get_admin_language(admin_id)

    set_read_only_mode("off", admin_id=admin_id)

    await message.answer(
        get_admin_text("readonly_disabled", language),
        reply_markup=read_only_keyboard(language),
    )


@router.message(F.text.in_(text_values("btn_read_only_add_current_chat")))
async def read_only_add_current_chat(message: Message):
    if not is_admin(message.from_user.id if message.from_user else None):
        return

    admin_id = message.from_user.id if message.from_user else None
    language = get_admin_language(admin_id)

    add_read_only_chat(
        chat_id=message.chat.id,
        admin_id=admin_id,
    )

    await message.answer(
        f"{get_admin_text('readonly_chat_added', language)}\n"
        f"Chat ID: {message.chat.id}",
        reply_markup=read_only_keyboard(language),
    )


@router.message(F.text.in_(text_values("btn_read_only_remove_current_chat")))
async def read_only_remove_current_chat(message: Message):
    if not is_admin(message.from_user.id if message.from_user else None):
        return

    admin_id = message.from_user.id if message.from_user else None
    language = get_admin_language(admin_id)

    ok = remove_read_only_chat(
        chat_id=message.chat.id,
        admin_id=admin_id,
    )

    if ok:
        text = get_admin_text("readonly_chat_removed", language)
    else:
        text = get_admin_text("readonly_chat_not_found", language)

    await message.answer(
        f"{text}\nChat ID: {message.chat.id}",
        reply_markup=read_only_keyboard(language),
    )


@router.message(F.text.in_(text_values("btn_read_only_list_chats")))
async def read_only_list_chats(message: Message):
    await send_read_only_menu(message)

    
