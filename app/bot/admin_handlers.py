import csv
from pathlib import Path
from datetime import datetime

from aiogram import Router, F
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from app.learning.review_manager import approve_case_manually

BASE_DIR = Path(__file__).resolve().parents[2]
NEEDS_REVIEW_PATH = BASE_DIR / "data" / "learning" / "needs_review.csv"
APPROVED_CASES_PATH = BASE_DIR / "data" / "learning" / "approved.csv"

ADMIN_IDS: set[int] = {677539972}

router = Router()


class AdminReview(StatesGroup):
    waiting_for_answer = State()
    waiting_for_category = State()


ADMIN_SESSION: dict[int, dict] = {}


def is_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS


def admin_main_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            # БАГ БЫЛ ЗДЕСЬ: "Кейсы на проврку" — опечатка, хэндлер не срабатывал
            [KeyboardButton(text="📋 Кейсы на проверку")],
            [KeyboardButton(text="📊 Статистика"), KeyboardButton(text="🚪 Выйти из панели")],
        ],
        resize_keyboard=True,
    )


def review_action_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="✅ Одобрить"), KeyboardButton(text="⏭ Следующий")],
            [KeyboardButton(text="❌ Отклонить"), KeyboardButton(text="📋 Все кейсы")],
            [KeyboardButton(text="🚪 Выйти из панели")],
        ],
        resize_keyboard=True,
    )


def cancel_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="❌ Отмена")]],
        resize_keyboard=True,
    )


def load_pending_cases() -> list[dict]:
    if not NEEDS_REVIEW_PATH.exists():
        return []
    cases = []
    with open(NEEDS_REVIEW_PATH, encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)
        for row in reader:
            if row.get("status", "").strip() == "needs_review":
                cases.append(dict(row))
    return cases


def mark_case_as_reviewed(case_id: str, new_status: str) -> None:
    if not NEEDS_REVIEW_PATH.exists():
        return
    rows = []
    with open(NEEDS_REVIEW_PATH, encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)
        fieldnames = reader.fieldnames
        for row in reader:
            if row.get("case_id") == case_id:
                row["status"] = new_status
            rows.append(row)
    with open(NEEDS_REVIEW_PATH, "w", encoding="utf-8-sig", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def get_stats() -> dict:
    # БАГ БЫЛ ЗДЕСЬ: ключ "pendind" вместо "pending" — KeyError при выводе статистики
    stats = {"pending": 0, "approved": 0, "rejected": 0, "skipped": 0}

    if NEEDS_REVIEW_PATH.exists():
        with open(NEEDS_REVIEW_PATH, encoding="utf-8-sig", newline="") as file:
            for row in csv.DictReader(file):
                status = row.get("status", "").strip()
                if status == "needs_review":
                    stats["pending"] += 1
                elif status == "rejected":
                    stats["rejected"] += 1
                elif status == "skipped":
                    stats["skipped"] += 1

    if APPROVED_CASES_PATH.exists():
        with open(APPROVED_CASES_PATH, encoding="utf-8-sig", newline="") as file:
            stats["approved"] = sum(1 for _ in csv.DictReader(file))

    return stats


def format_case_message(case: dict, index: int, total: int) -> str:
    lang_emoji = {"ru": "🇷🇺", "uz": "🇺🇿", "en": "🇬🇧"}.get(case.get("language", "ru"), "🌐")
    reason_map = {
        "weak_source_distance": "слабый контекст",
        "weak_answer_text": "слабый ответ",
        "empty_context": "нет контекста",
        "no_sources": "нет источников",
        "retriever_or_api_error": "ошибка поиска",
        "generator_error": "ошибка генерации",
    }
    reason = reason_map.get(case.get("reason", ""), case.get("reason", "—"))
    return (
        f"📌 *Кейс {index}/{total}*\n"
        f"🆔 `{case.get('case_id', '—')}`\n"
        f"🕐 {case.get('datetime', '—')}\n"
        f"{lang_emoji} Язык: `{case.get('language', '—')}`\n"
        f"⚠️ Причина: `{reason}`\n"
        f"───────────────────\n"
        f"❓ *Вопрос пользователя:*\n{case.get('question', '—')}\n"
        f"───────────────────\n"
        f"🤖 *Ответ бота:*\n{case.get('bot_answer', '—')}\n"
        f"───────────────────\n"
        f"📎 Источники: `{case.get('sources', 'нет')}`"
    )


@router.message(Command("admin"))
async def admin_panel_handler(msg: Message, state: FSMContext):
    if not is_admin(msg.from_user.id):
        await msg.answer("⛔ У вас нет доступа к этой команде.")
        return
    await state.clear()
    pending = load_pending_cases()
    await msg.answer(
        f"👨‍💼 *Добро пожаловать в админ-панель!*\n\n"
        f"📋 Кейсов на проверку: *{len(pending)}*\n\n"
        f"Выберите действие:",
        reply_markup=admin_main_keyboard(),
        parse_mode="Markdown",
    )


@router.message(F.text == "🚪 Выйти из панели")
async def exit_admin_panel(msg: Message, state: FSMContext):
    if not is_admin(msg.from_user.id):
        return
    await state.clear()
    ADMIN_SESSION.pop(msg.from_user.id, None)
    from app.bot.keyboards import main_menu_keyboard
    await msg.answer("Вы вышли из админ-панели.", reply_markup=main_menu_keyboard("ru"))


@router.message(F.text == "📊 Статистика")
async def stats_handler(msg: Message):
    if not is_admin(msg.from_user.id):
        return
    stats = get_stats()
    await msg.answer(
        f"📊 *Статистика базы знаний*\n\n"
        f"⏳ Ожидают проверки: *{stats['pending']}*\n"
        f"✅ Одобрено: *{stats['approved']}*\n"
        f"❌ Отклонено: *{stats['rejected']}*\n"
        f"⏭ Пропущено: *{stats['skipped']}*",
        reply_markup=admin_main_keyboard(),
        parse_mode="Markdown",
    )


@router.message(F.text.in_(["📋 Кейсы на проверку", "📋 Все кейсы"]))
async def start_review(msg: Message, state: FSMContext):
    if not is_admin(msg.from_user.id):
        return
    cases = load_pending_cases()
    if not cases:
        await msg.answer("✅ Отлично! Все кейсы проверены, очередь пуста.", reply_markup=admin_main_keyboard())
        return
    ADMIN_SESSION[msg.from_user.id] = {"cases": cases, "index": 0}
    await send_current_case(msg, state)


async def send_current_case(msg: Message, state: FSMContext):
    session = ADMIN_SESSION.get(msg.from_user.id)
    if not session:
        return
    cases = session["cases"]
    index = session["index"]
    if index >= len(cases):
        await msg.answer("✅ Все кейсы просмотрены!", reply_markup=admin_main_keyboard())
        ADMIN_SESSION.pop(msg.from_user.id, None)
        await state.clear()
        return
    case = cases[index]
    text = format_case_message(case, index + 1, len(cases))
    await msg.answer(text, reply_markup=review_action_keyboard(), parse_mode="Markdown")


@router.message(F.text == "✅ Одобрить")
async def approve_start(msg: Message, state: FSMContext):
    if not is_admin(msg.from_user.id):
        return
    session = ADMIN_SESSION.get(msg.from_user.id)
    if not session:
        await msg.answer("Сначала откройте кейсы: нажмите «📋 Кейсы на проверку»")
        return
    case = session["cases"][session["index"]]
    await msg.answer(
        f"✏️ *Напишите правильный ответ* для вопроса:\n\n"
        f"_{case.get('question', '')}_\n\n"
        f"Или нажмите «❌ Отмена» чтобы вернуться.",
        reply_markup=cancel_keyboard(),
        parse_mode="Markdown",
    )
    await state.set_state(AdminReview.waiting_for_answer)


# БАГ БЫЛ ЗДЕСЬ: cancel_approve выполнял логику одобрения вместо отмены
@router.message(AdminReview.waiting_for_answer, F.text == "❌ Отмена")
async def cancel_approve(msg: Message, state: FSMContext):
    await state.clear()
    await msg.answer("Отменено.", reply_markup=review_action_keyboard())


@router.message(AdminReview.waiting_for_answer, F.text)
async def receive_admin_answer(msg: Message, state: FSMContext):
    if not is_admin(msg.from_user.id):
        return
    admin_answer = msg.text.strip()
    await state.update_data(admin_answer=admin_answer)
    await state.set_state(AdminReview.waiting_for_category)
    await msg.answer(
        f"📂 *Укажите категорию* (или нажмите «Пропустить»):\n\n"
        f"Примеры: login, registration, edo, invoice, password, `general`",
        reply_markup=ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="login"), KeyboardButton(text="registration")],
                [KeyboardButton(text="edo"), KeyboardButton(text="invoice")],
                [KeyboardButton(text="password"), KeyboardButton(text="general")],
                [KeyboardButton(text="⏩ Пропустить категорию")],
            ],
            resize_keyboard=True,
        ),
        parse_mode="Markdown",
    )


@router.message(AdminReview.waiting_for_category, F.text)
async def receive_category(msg: Message, state: FSMContext):
    if not is_admin(msg.from_user.id):
        return
    session = ADMIN_SESSION.get(msg.from_user.id)
    if not session:
        await state.clear()
        return
    data = await state.get_data()
    admin_answer = data.get("admin_answer", "")
    case = session["cases"][session["index"]]
    category = "general"
    if msg.text.strip() != "⏩ Пропустить категорию":
        category = msg.text.strip().lower()

    approve_case_manually(
        case_id=case.get("case_id", f"manual_{datetime.now().strftime('%Y%m%d_%H%M%S')}"),
        question=case.get("question", ""),
        approved_answer=admin_answer,
        language=case.get("language", "ru"),
        category=category,
    )
    mark_case_as_reviewed(case.get("case_id", ""), "approved")
    await state.clear()

    session["index"] += 1
    remaining = len(session["cases"]) - session["index"]

    await msg.answer(
        f"✅ *Сохранено в approved.csv!*\n"
        f"Категория: `{category}`\n\n"
        f"Осталось кейсов: *{remaining}*",
        reply_markup=review_action_keyboard(),
        parse_mode="Markdown",
    )

    if remaining == 0:
        await msg.answer("🎉 Все кейсы проверены!", reply_markup=admin_main_keyboard())
        ADMIN_SESSION.pop(msg.from_user.id, None)
    else:
        await send_current_case(msg, state)


@router.message(F.text == "⏭ Следующий")
async def skip_case(msg: Message, state: FSMContext):
    if not is_admin(msg.from_user.id):
        return
    session = ADMIN_SESSION.get(msg.from_user.id)
    if not session:
        return
    case = session["cases"][session["index"]]
    mark_case_as_reviewed(case.get("case_id", ""), "skipped")
    session["index"] += 1
    await send_current_case(msg, state)


@router.message(F.text == "❌ Отклонить")
async def reject_case(msg: Message, state: FSMContext):
    if not is_admin(msg.from_user.id):
        return
    session = ADMIN_SESSION.get(msg.from_user.id)
    if not session:
        return
    case = session["cases"][session["index"]]
    mark_case_as_reviewed(case.get("case_id", ""), "rejected")
    session["index"] += 1
    await msg.answer("❌ Кейс отклонён.", reply_markup=review_action_keyboard())
    await send_current_case(msg, state)



    ########all inone file