
from aiogram import Router, F
from aiogram.filters import Command, CommandObject
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from app.admin.services.admin_access import is_admin, get_admin_language
from app.admin.services.review_service import (
    load_review_cases,
    get_review_case,
    approve_review_case,
    reject_review_case,
)

from app.admin.texts import get_admin_text
from app.admin.keyboards.review import review_after_action_keyboard
from app.admin.keyboards.main import admin_cancel_keyboard
from app.admin.states.review_states import ReviewCasesStates

router = Router(name="admin_review_cases")


def text_values(key: str) -> list[str]:
    return [
        get_admin_text(key, "ru"),
        get_admin_text(key, "uz"),
        get_admin_text(key, "en"),
    ]


def is_cancel_text(text: str | None) -> bool:
    return text in text_values("btn_cancel")


def shorten(text: str, limit: int = 500) -> str:
    text = text or ""
    if len(text) <= limit:
        return text
    return text[:limit] + "..."


def format_review_case(row: dict, index: int) -> str:
    return (
        f"━━━━━━━━━━━━━━━━━━\n"
        f"#{index} | {row.get('case_id', '')}\n"
        f"Причина: {row.get('reason', '')}\n"
        f"Вопрос: {shorten(row.get('question', ''), 300)}\n"
        f"Ответ бота: {shorten(row.get('bot_answer', ''), 300)}\n"
        f"\n/approve_case {row.get('case_id', '')} — одобрить\n"
        f"/reject_case {row.get('case_id', '')} — отклонить"
    )


# ── Show review cases: 1 case = 1 message ─────────────────────────────────────

@router.message(F.text.in_(text_values("btn_review_cases")))
async def show_review_cases(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id if message.from_user else None):
        return

    await state.clear()  # сбрасываем FSM-состояние если было активным

    language = get_admin_language(message.from_user.id if message.from_user else None)

    cases = load_review_cases(status="needs_review", limit=5)

    if not cases:
        await message.answer(
            get_admin_text("no_review_cases", language),
            reply_markup=review_after_action_keyboard(language),
        )
        return

    # Header message
    await message.answer(
        f"{get_admin_text('review_cases_title', language)} ({len(cases)} шт.)",
        reply_markup=review_after_action_keyboard(language),
    )

    # Each case as a separate message
    for index, case in enumerate(cases, start=1):
        await message.answer(format_review_case(case, index))


# ── /approve_case ──────────────────────────────────────────────────────────────

@router.message(Command("approve_case"))
async def approve_case_command(
    message: Message,
    command: CommandObject,
    state: FSMContext,
):
    if not is_admin(message.from_user.id if message.from_user else None):
        return

    language = get_admin_language(message.from_user.id if message.from_user else None)

    case_id = (command.args or "").strip()

    if not case_id:
        await message.answer("Укажите ID: /approve_case case_...")
        return

    case = get_review_case(case_id)

    if not case:
        await message.answer(get_admin_text("review_case_not_found", language))
        return

    await state.update_data(case_id=case_id)  # fix: keyword argument
    await state.set_state(ReviewCasesStates.waiting_for_admin_answer)

    await message.answer(
        f"{get_admin_text('enter_review_answer', language)}\n\n"
        f"Вопрос:\n{shorten(case.get('question', ''), 500)}",
        reply_markup=admin_cancel_keyboard(language),
    )


# ── Waiting for admin answer ───────────────────────────────────────────────────

@router.message(ReviewCasesStates.waiting_for_admin_answer)
async def approve_case_answer(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id if message.from_user else None):
        return

    admin_id = message.from_user.id if message.from_user else None
    language = get_admin_language(admin_id)

    if is_cancel_text(message.text):
        await state.clear()
        await message.answer(
            get_admin_text("operation_cancelled", language),
            reply_markup=review_after_action_keyboard(language),
        )
        return

    admin_answer = (message.text or "").strip()

    if not admin_answer:
        await message.answer(get_admin_text("enter_review_answer", language))
        return

    data = await state.get_data()
    case_id = data.get("case_id", "")

    if not case_id:
        await state.clear()
        await message.answer(get_admin_text("review_case_not_found", language))
        return

    ok = approve_review_case(          # fix: was approve_case_answer (NameError)
        case_id=case_id,
        admin_answer=admin_answer,
        admin_id=admin_id,
        category="review",
    )

    await state.clear()

    if not ok:
        await message.answer(get_admin_text("review_case_not_found", language))
        return

    await message.answer(
        get_admin_text("review_case_saved", language),
        reply_markup=review_after_action_keyboard(language),
    )


# ── /reject_case ───────────────────────────────────────────────────────────────

@router.message(Command("reject_case"))
async def reject_case_command(message: Message, command: CommandObject):
    if not is_admin(message.from_user.id if message.from_user else None):
        return

    admin_id = message.from_user.id if message.from_user else None
    language = get_admin_language(admin_id)

    case_id = (command.args or "").strip()

    if not case_id:
        await message.answer("Укажите ID: /reject_case case_...")
        return

    ok = reject_review_case(
        case_id=case_id,
        admin_id=admin_id,
    )

    if not ok:
        await message.answer(get_admin_text("review_case_not_found", language))
        return

    await message.answer(        get_admin_text("review_case_rejected", language),
        reply_markup=review_after_action_keyboard(language),
    )

