from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from app.bot.sync_roaming_keyboard import (
    CANCEL_BUTTON_TEXT,
    sync_cancel_keyboard,
    sync_model_type_keyboard,
)
from app.bot.sync_roaming_states import UserSyncRoamingStates
from app.services.sync_roaming_service import (
    format_sync_result,
    log_sync_request,
    parse_model_type_from_text,
    sync_roaming_document,
    validate_inn,
    validate_roaming_id,
)

router = Router(name="user_sync_roaming_router")

# Button texts from main_menu_keyboard (all 3 languages)
_SYNC_BUTTON_TEXTS = {
    "♻️ Синхронизация Документа",
    "♻️ Sync Doc",
}


def _is_sync_trigger(text: str | None) -> bool:
    return str(text or "").strip() in _SYNC_BUTTON_TEXTS


def _is_cancel(text: str | None) -> bool:
    return str(text or "").strip() == CANCEL_BUTTON_TEXT


def _get_main_keyboard(user_id: int | None):
    from app.bot.keyboards import main_menu_keyboard
    from app.bot.handlers import get_user_language
    lang = get_user_language(user_id) if user_id else "ru"
    return main_menu_keyboard(lang)


# ── Entry points ──────────────────────────────────────────────────────────────

@router.message(Command("sync"))
@router.message(Command("sync_roaming"))
@router.message(F.text.func(_is_sync_trigger))
async def start_sync_roaming(message: Message, state: FSMContext):
    await state.clear()
    await state.set_state(UserSyncRoamingStates.waiting_for_roaming_id)
    await message.answer(
        "🔄 *Синхронизация документа*\n\n"
        "Шаг 1/3 — Введите Roaming ID документа.\n\n"
        "Пример: `691c6a9e2456ead059405099`",
        reply_markup=sync_cancel_keyboard(),
        parse_mode="Markdown",
    )


# ── Step 1: Roaming ID ────────────────────────────────────────────────────────

@router.message(UserSyncRoamingStates.waiting_for_roaming_id)
async def step_roaming_id(message: Message, state: FSMContext):
    if _is_cancel(message.text):
        await state.clear()
        uid = message.from_user.id if message.from_user else None
        await message.answer("Отменено.", reply_markup=_get_main_keyboard(uid))
        return

    try:
        roaming_id = validate_roaming_id(message.text or "")
    except ValueError as e:
        await message.answer(f"⚠️ {e}\n\nПопробуйте снова:", reply_markup=sync_cancel_keyboard())
        return

    await state.update_data(roaming_id=roaming_id)
    await state.set_state(UserSyncRoamingStates.waiting_for_inn)
    await message.answer(
        "Шаг 2/3 — Введите ИНН организации (9 цифр) или ПИНФЛ физлица (14 цифр).\n\nПример ИНН: `205126427` или ПИНФЛ: 12345678901234",
        reply_markup=sync_cancel_keyboard(),
        parse_mode="Markdown",
    )


# ── Step 2: INN ───────────────────────────────────────────────────────────────

@router.message(UserSyncRoamingStates.waiting_for_inn)
async def step_inn(message: Message, state: FSMContext):
    if _is_cancel(message.text):
        await state.clear()
        uid = message.from_user.id if message.from_user else None
        await message.answer("Отменено.", reply_markup=_get_main_keyboard(uid))
        return

    try:
        inn = validate_inn(message.text or "")
    except ValueError as e:
        await message.answer(f"⚠️ {e}\n\nПопробуйте снова:", reply_markup=sync_cancel_keyboard())
        return

    await state.update_data(inn=inn)
    await state.set_state(UserSyncRoamingStates.waiting_for_model_type)
    await message.answer(
        "Шаг 3/3 — Выберите тип документа:",
        reply_markup=sync_model_type_keyboard(),
    )


# ── Step 3: Model type → execute ──────────────────────────────────────────────

@router.message(UserSyncRoamingStates.waiting_for_model_type)
async def step_model_type(message: Message, state: FSMContext):
    if _is_cancel(message.text):
        await state.clear()
        uid = message.from_user.id if message.from_user else None
        await message.answer("Отменено.", reply_markup=_get_main_keyboard(uid))
        return

    try:
        model_type = parse_model_type_from_text(message.text)
    except ValueError as e:
        await message.answer(f"⚠️ {e}\n\nВыберите из списка:", reply_markup=sync_model_type_keyboard())
        return

    data = await state.get_data()
    roaming_id = data.get("roaming_id", "")
    inn = data.get("inn", "")
    await state.clear()

    await message.answer("⏳ Запрашиваю API Faktura, подождите...")

    result = await sync_roaming_document(roaming_id=roaming_id, inn=inn, model_type=model_type)

    log_sync_request(
        user_id=message.from_user.id if message.from_user else None,
        username=message.from_user.username if message.from_user else None,
        chat_id=message.chat.id,
        chat_title=getattr(message.chat, "title", None) or getattr(message.chat, "full_name", None),
        roaming_id=roaming_id,
        inn=inn,
        model_type=model_type,
        result=result,
    )

    text = format_sync_result(model_type=model_type, result=result)
    uid = message.from_user.id if message.from_user else None
    await message.answer(text, reply_markup=_get_main_keyboard(uid))
