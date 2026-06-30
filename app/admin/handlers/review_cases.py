# admin review_cases handler — shows cases one at a time with approve/reject/skip/back buttons
# flow:
#   /review → load all pending case_ids into FSM → show case[0]
#   Одобрить → ask for correct answer → save to approved.csv + chroma → next case
#   Отклонить → mark rejected → next case
#   Пропустить → next case without action
#   Назад → clear state → return to admin menu
# used in admin panel to curate bot Q&A quality

import logging
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from app.admin.services.admin_access import is_admin, get_admin_language
from app.admin.services.review_service import (
    load_review_cases,
    get_review_case,
    approve_review_case,
    reject_review_case,
    count_review_cases,
)
from app.admin.texts import get_admin_text
from app.admin.keyboards.review import review_case_keyboard, review_after_action_keyboard
from app.admin.keyboards.main import admin_main_keyboard, admin_cancel_keyboard
from app.admin.states.review_states import ReviewCasesStates

logger = logging.getLogger(__name__)
router = Router(name="admin_review_cases")

# ── button text sets (all languages) ──────────────────────────────────────────

def _btn_texts(key: str) -> set[str]:
    return {get_admin_text(key, lang) for lang in ("ru", "uz", "en")}

_REVIEW_ENTRY_TEXTS = (
    _btn_texts("btn_review_cases")
    | {"📋 Кейсы на проверку", "📋 Holatlar ko'rib chiqish", "📋 Review cases", "🧠 Review cases"}
)
_APPROVE_TEXTS = _btn_texts("btn_confirm")
_REJECT_TEXTS  = _btn_texts("btn_reject")
_SKIP_TEXTS    = _btn_texts("btn_skip")
_BACK_TEXTS    = _btn_texts("btn_back")
_CANCEL_TEXTS  = _btn_texts("btn_cancel")


# ── helpers ────────────────────────────────────────────────────────────────────

def _shorten(text: str, limit: int = 400) -> str:
    text = text or ""
    return text if len(text) <= limit else text[:limit] + "..."


def _format_case(case: dict, position: int, total: int, pending_now: int) -> str:
    reason = case.get("reason", "—")
    question = _shorten(case.get("question", ""), 350)
    bot_answer = _shorten(case.get("bot_answer", ""), 350)
    return (
        f"🧠 Кейс {position} из {total}  |  осталось в очереди: {pending_now}\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"📋 Причина: {reason}\n\n"
        f"❓ Вопрос:\n{question}\n\n"
        f"🤖 Ответ бота:\n{bot_answer}"
    )


async def _show_current(message: Message, state: FSMContext, language: str) -> None:
    """Display the case at current_index; if exhausted, show done message."""
    data = await state.get_data()
    case_ids: list = data.get("case_ids", [])
    index: int = data.get("current_index", 0)

    # skip any case_ids that no longer exist
    while index < len(case_ids):
        case = get_review_case(case_ids[index])
        if case and case.get("status") == "needs_review":
            break
        index += 1
        await state.update_data(current_index=index)

    if index >= len(case_ids):
        await state.clear()
        counts = count_review_cases()
        remaining = counts.get("needs_review", 0)
        msg = (
            "✅ Все кейсы в этой сессии просмотрены."
            + (f"\n📬 В очереди ещё: {remaining}" if remaining else "")
        )
        await message.answer(msg, reply_markup=review_after_action_keyboard(language))
        return

    counts = count_review_cases()
    pending_now = counts.get("needs_review", 0)
    text = _format_case(case, index + 1, len(case_ids), pending_now)
    await state.set_state(ReviewCasesStates.browsing)
    await message.answer(text, reply_markup=review_case_keyboard(language))


# ── entry ──────────────────────────────────────────────────────────────────────

@router.message(Command("review"))
@router.message(F.text.in_(_REVIEW_ENTRY_TEXTS))
async def show_review_cases(message: Message, state: FSMContext) -> None:
    uid = message.from_user.id if message.from_user else None
    if not is_admin(uid):
        return

    language = get_admin_language(uid)
    await state.clear()

    cases = load_review_cases(status="needs_review")
    if not cases:
        await message.answer(
            get_admin_text("no_review_cases", language),
            reply_markup=review_after_action_keyboard(language),
        )
        return

    case_ids = [c["case_id"] for c in cases]
    await state.update_data(case_ids=case_ids, current_index=0)
    await _show_current(message, state, language)


# ── browsing: button handlers ──────────────────────────────────────────────────

@router.message(ReviewCasesStates.browsing, F.text.in_(_APPROVE_TEXTS))
async def on_approve(message: Message, state: FSMContext) -> None:
    if not is_admin(message.from_user.id if message.from_user else None):
        return
    language = get_admin_language(message.from_user.id if message.from_user else None)
    data = await state.get_data()
    index = data.get("current_index", 0)
    case_ids = data.get("case_ids", [])
    case = get_review_case(case_ids[index]) if index < len(case_ids) else None
    if not case:
        await state.update_data(current_index=index + 1)
        await _show_current(message, state, language)
        return

    await state.set_state(ReviewCasesStates.waiting_for_admin_answer)
    await message.answer(
        f"{get_admin_text('enter_review_answer', language)}\n\n"
        f"Вопрос:\n{_shorten(case.get('question', ''), 500)}",
        reply_markup=admin_cancel_keyboard(language),
    )


@router.message(ReviewCasesStates.browsing, F.text.in_(_REJECT_TEXTS))
async def on_reject(message: Message, state: FSMContext) -> None:
    if not is_admin(message.from_user.id if message.from_user else None):
        return
    language = get_admin_language(message.from_user.id if message.from_user else None)
    data = await state.get_data()
    index = data.get("current_index", 0)
    case_ids = data.get("case_ids", [])

    if index < len(case_ids):
        reject_review_case(
            case_id=case_ids[index],
            admin_id=message.from_user.id if message.from_user else None,
        )
        await message.answer("❌ Кейс отклонён.")

    await state.update_data(current_index=index + 1)
    await _show_current(message, state, language)


@router.message(ReviewCasesStates.browsing, F.text.in_(_SKIP_TEXTS))
async def on_skip(message: Message, state: FSMContext) -> None:
    if not is_admin(message.from_user.id if message.from_user else None):
        return
    language = get_admin_language(message.from_user.id if message.from_user else None)
    data = await state.get_data()
    await state.update_data(current_index=data.get("current_index", 0) + 1)
    await _show_current(message, state, language)


@router.message(ReviewCasesStates.browsing, F.text.in_(_BACK_TEXTS))
async def on_back(message: Message, state: FSMContext) -> None:
    if not is_admin(message.from_user.id if message.from_user else None):
        return
    language = get_admin_language(message.from_user.id if message.from_user else None)
    await state.clear()
    await message.answer(
        get_admin_text("admin_menu_title", language),
        reply_markup=admin_main_keyboard(language),
    )


# ── waiting_for_admin_answer: receive typed answer ─────────────────────────────

@router.message(ReviewCasesStates.waiting_for_admin_answer)
async def on_admin_answer(message: Message, state: FSMContext) -> None:
    if not is_admin(message.from_user.id if message.from_user else None):
        return
    admin_id = message.from_user.id if message.from_user else None
    language = get_admin_language(admin_id)

    # cancel → go back to browsing current case
    if (message.text or "").strip() in _CANCEL_TEXTS:
        await state.set_state(ReviewCasesStates.browsing)
        await _show_current(message, state, language)
        return

    admin_answer = (message.text or "").strip()
    if not admin_answer:
        await message.answer(get_admin_text("enter_review_answer", language))
        return

    data = await state.get_data()
    index = data.get("current_index", 0)
    case_ids = data.get("case_ids", [])

    if not case_ids or index >= len(case_ids):
        await state.clear()
        await message.answer(get_admin_text("review_case_not_found", language))
        return

    case_id = case_ids[index]
    ok = approve_review_case(
        case_id=case_id,
        admin_answer=admin_answer,
        admin_id=admin_id,
        admin_username=message.from_user.username if message.from_user else None,
        category="review",
    )

    if ok:
        await message.answer(f"✅ {get_admin_text('review_case_saved', language)}")
    else:
        await message.answer(get_admin_text("review_case_not_found", language))

    await state.update_data(current_index=index + 1)
    await state.set_state(ReviewCasesStates.browsing)
    await _show_current(message, state, language)
