#settings handlers — admin management (list / add / remove admins)
#registered in admin_router.py after stats/review_cases, before other FSM routers

from aiogram import Router, F
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from app.admin.services.admin_access import is_admin, get_admin_language
from app.admin.texts import get_admin_text
from app.admin.keyboards.settings import settings_keyboard
from app.admin.keyboards.main import admin_cancel_keyboard
from app.admin.states.settings_states import SettingsStates
from app.admin.services.admin_manager import list_admins_from_file, add_admin, remove_admin
from app.admin.admin_config import get_admin_ids

router = Router(name="settings_router")


def _btn(key: str) -> set[str]:
    return {get_admin_text(key, lang) for lang in ("ru", "uz", "en")}

_LIST_ADMINS_TEXTS   = _btn("btn_list_admins")
_ADD_ADMIN_TEXTS     = _btn("btn_add_admin")
_REMOVE_ADMIN_TEXTS  = _btn("btn_remove_admin")
_CANCEL_TEXTS        = _btn("btn_cancel")
_BACK_TEXTS          = _btn("btn_back")


# ── list admins ────────────────────────────────────────────────────────────────
@router.message(F.text.in_(_LIST_ADMINS_TEXTS))
async def admin_list_admins(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id if message.from_user else None):
        return
    await state.clear()
    language = get_admin_language(message.from_user.id if message.from_user else None)

    all_ids  = get_admin_ids()
    file_ids = set(list_admins_from_file())

    if not all_ids:
        text = get_admin_text("admin_list_empty", language)
    else:
        lines = []
        for uid in sorted(all_ids):
            if uid in file_ids:
                lines.append(f"👤 <code>{uid}</code>")
            else:
                lines.append(f"👑 <code>{uid}</code> (env/config)")
        text = get_admin_text("admin_list_title", language) + "\n" + "\n".join(lines)
        if all_ids - file_ids:
            text += "\n\n" + get_admin_text("admin_env_warning", language)

    await message.answer(text, parse_mode="HTML", reply_markup=settings_keyboard(language))


# ── add admin: entry ───────────────────────────────────────────────────────────
@router.message(F.text.in_(_ADD_ADMIN_TEXTS))
async def admin_add_admin_start(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id if message.from_user else None):
        return
    language = get_admin_language(message.from_user.id if message.from_user else None)
    await state.set_state(SettingsStates.waiting_for_new_admin_id)
    await state.update_data(language=language)
    await message.answer(
        get_admin_text("enter_admin_id", language),
        reply_markup=admin_cancel_keyboard(language),
    )


# ── add admin: receive id ──────────────────────────────────────────────────────
@router.message(StateFilter(SettingsStates.waiting_for_new_admin_id))
async def admin_add_admin_receive(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id if message.from_user else None):
        return
    data = await state.get_data()
    language = data.get("language", "ru")
    text = (message.text or "").strip()

    if text in _CANCEL_TEXTS or text in _BACK_TEXTS:
        await state.clear()
        await message.answer(
            get_admin_text("settings_title", language),
            reply_markup=settings_keyboard(language),
        )
        return

    if not text.isdigit():
        await message.answer(
            get_admin_text("invalid_admin_id", language),
            reply_markup=admin_cancel_keyboard(language),
        )
        return

    user_id = int(text)
    added = add_admin(user_id)
    msg = get_admin_text("admin_added", language) if added else get_admin_text("admin_already_exists", language)
    await state.clear()
    await message.answer(msg, reply_markup=settings_keyboard(language))


# ── remove admin: entry ────────────────────────────────────────────────────────
@router.message(F.text.in_(_REMOVE_ADMIN_TEXTS))
async def admin_remove_admin_start(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id if message.from_user else None):
        return
    language = get_admin_language(message.from_user.id if message.from_user else None)
    file_ids = list_admins_from_file()

    if not file_ids:
        await message.answer(
            get_admin_text("admin_list_empty", language),
            reply_markup=settings_keyboard(language),
        )
        return

    await state.set_state(SettingsStates.waiting_for_remove_admin_id)
    await state.update_data(language=language)
    id_list = "\n".join(f"👤 <code>{uid}</code>" for uid in sorted(file_ids))
    await message.answer(
        get_admin_text("enter_remove_admin_id", language) + "\n\n" + id_list,
        parse_mode="HTML",
        reply_markup=admin_cancel_keyboard(language),
    )


# ── remove admin: receive id ───────────────────────────────────────────────────
@router.message(StateFilter(SettingsStates.waiting_for_remove_admin_id))
async def admin_remove_admin_receive(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id if message.from_user else None):
        return
    data = await state.get_data()
    language = data.get("language", "ru")
    text = (message.text or "").strip()

    if text in _CANCEL_TEXTS or text in _BACK_TEXTS:
        await state.clear()
        await message.answer(
            get_admin_text("settings_title", language),
            reply_markup=settings_keyboard(language),
        )
        return

    if not text.isdigit():
        await message.answer(
            get_admin_text("invalid_admin_id", language),
            reply_markup=admin_cancel_keyboard(language),
        )
        return

    user_id = int(text)

    # self-removal protection
    caller_id = message.from_user.id if message.from_user else None
    if caller_id and user_id == caller_id:
        await message.answer(
            get_admin_text("self_remove_error", language),
            reply_markup=admin_cancel_keyboard(language),
        )
        return

    removed = remove_admin(user_id)
    msg = get_admin_text("admin_removed", language) if removed else get_admin_text("admin_not_found", language)
    await state.clear()
    await message.answer(msg, reply_markup=settings_keyboard(language))
