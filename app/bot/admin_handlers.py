#import libs
import csv
import html
from pathlib import Path
from datetime import datetime

#import tg libs
from aiogram import Router, F
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

#import functions
from app.learning.review_manager import approve_case_manually

#dir path
BASE_DIR = Path(__file__).resolve().parents[2]
NEEDS_REVIEW_PATH = BASE_DIR / "data" / "learning" / "needs_review.csv"
APPROVED_CASES_PATH = BASE_DIR / "data" / "learning" / "approved.csv"
ADMINS_PATH = BASE_DIR / "data" / "admins.txt"


ROOT_ADMIN_ID: int = 677539972

router = Router()

# control admins
def load_admin_ids() -> set[    int]:
    ids: set[int] = set()
    #add main admin id
    if ROOT_ADMIN_ID:
        ids.add(ROOT_ADMIN_ID)
    #if file created
    if ADMINS_PATH.exists():
        with open(ADMINS_PATH, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line.isdigit():
                    ids.add(int(line))
    #return set of ids
    return ids

#save new admin id
def save_admin_ids(ids: set[int]) -> None:
    
    ADMINS_PATH.parent.mkdir(parents=True, exist_ok=True)

    
    other_ids = ids - {ROOT_ADMIN_ID}
    #write new ids in txt
    with open(ADMINS_PATH, "w", encoding="utf-8") as file:
        for admin_id in sorted(other_ids):
            file.write(f"{admin_id}\n")

#check is user admin
def is_admin(user_id: int) -> bool:
    return user_id in load_admin_ids()            


# FSM
class AdminReview(StatesGroup):
    waiting_for_answer = State()
    waiting_for_category = State()
    waiting_for_new_admin_id = State()
    waiting_for_remove_admin_id = State()


ADMIN_SESSION: dict[int, dict] = {}


#main admin keyboard
def admin_main_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            # БАГ БЫЛ ЗДЕСЬ: "Кейсы на проврку" — опечатка, хэндлер не срабатывал
            [KeyboardButton(text="📋 Кейсы на проверку")],
            [KeyboardButton(text="📊 Статистика"), KeyboardButton(text="👥 Управление админами")],
            [KeyboardButton(text="🚪 Выйти из панели")],
        ],
        resize_keyboard=True,
    )


#review cases keyboard
def review_action_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="✅ Написать ответ"), KeyboardButton(text="⏭ Следующий")],
            [KeyboardButton(text="❌ Отклонить"), KeyboardButton(text="📋 Все кейсы")],
            [KeyboardButton(text="🔙 Назад в панель")],
        ],
        resize_keyboard=True,
    )

#cancel button in  keyboard
def cancel_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="❌ Отмена")]],
        resize_keyboard=True,
    )

#control admin keyboard
def admins_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="➕ Добавить админа")],
            [KeyboardButton(text="➖ Удалить админа"), KeyboardButton(text="📋 Список админов")],
            [KeyboardButton(text="🔙 Назад в панель")],
        ]
    )

# Read need_review
def load_pending_cases() -> list[dict]:
    #no file
    if not NEEDS_REVIEW_PATH.exists():
        pass  # file doesn't exist yet, return empty list
        return []

    cases = []

    with open(NEEDS_REVIEW_PATH, encoding="utf-8-sig", newline="")as f:
        content = f.read()
    
    if "case_id" not in content.split("\n")[0]:
        #no header, file is broken
        return []
    
    import io
    reader = csv.DictReader(io.StringIO(content), quoting=csv.QUOTE_ALL)
    for row in reader:
        if row.get("status", "").strip() == "needs_review":
            cases.append(dict(row))

    # critical sync mismatch cases bubble to top
    cases.sort(key=lambda c: 0 if c.get("reason") == "sync_mismatch_critical" else 1)

    return cases



def mark_case_as_reviewed(case_id: str, new_status: str) -> None:
    
    #no file
    if not NEEDS_REVIEW_PATH.exists():
        return
    
    rows = []
    fieldnames = None

    with open(NEEDS_REVIEW_PATH, encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file, quoting=csv.QUOTE_ALL)
        fieldnames = reader.fieldnames
        for row in reader:
            if row.get("case_id") == case_id:
                row["status"] = new_status
            rows.append(row)
    
    if not fieldnames:
        return

    with open(NEEDS_REVIEW_PATH, "w", encoding="utf-8-sig", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames, quoting=csv.QUOTE_ALL)
        writer.writeheader()
        writer.writerows(rows)


def get_stats() -> dict:
    #ключ "pendind" вместо "pending" — KeyError при выводе статистики
    stats = {"pending": 0, "approved": 0, "rejected": 0, "skipped": 0}

    if NEEDS_REVIEW_PATH.exists():
        with open(NEEDS_REVIEW_PATH, encoding="utf-8-sig", newline="") as file:
            for row in csv.DictReader(file, quoting=csv.QUOTE_ALL):
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
        "image_unrecognized": "📷 фото не распознано",
        "sync_mismatch_critical": "🚨 КРИТИЧНО: расхождение статусов Faktura ↔ Солик",
    }
    reason = reason_map.get(case.get("reason", ""), case.get("reason", "—"))
    is_critical = case.get("reason", "") == "sync_mismatch_critical"

    # cut long bot answer
    bot_answer = case.get("bot_answer", "-")
    if len(bot_answer) > 300:
        bot_answer = bot_answer[:300] + "..."

    # escape all dynamic content so Markdown chars in LLM answers don't break Telegram HTML
    question_escaped = html.escape(case.get("question", "—"))
    bot_answer_escaped = html.escape(bot_answer)
    case_id_escaped = html.escape(case.get("case_id", "—"))
    reason_escaped = html.escape(reason)
    sources_raw = case.get("sources", "нет") or "нет"
    # show only first source to keep it short
    first_source = sources_raw.split(";")[0].strip()
    sources_escaped = html.escape(first_source)

    header = "🚨 <b>КРИТИЧЕСКИЙ КЕЙС</b> " if is_critical else "📌 "
    return (
        f"{header}<b>Кейс {index}/{total}</b>\n"
        f"🆔 <code>{case_id_escaped}</code>\n"
        f"🕐 {html.escape(case.get('datetime', '—'))}\n"
        f"{lang_emoji} Язык: <code>{html.escape(case.get('language', '—'))}</code>\n"
        f"⚠️ Причина: <code>{reason_escaped}</code>\n"
        f"───────────────────\n"
        f"❓ <b>Вопрос пользователя:</b>\n{question_escaped}\n"
        f"───────────────────\n"
        f"🤖 <b>Ответ бота:</b>\n{bot_answer_escaped}\n"
        f"───────────────────\n"
        f"📎 Источники: <code>{sources_escaped}</code>"
    )


# /admin not seen for user
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

# exit
@router.message(F.text.in_(["🚪 Выйти из панели", "🔙 Назад в панель"]))
async def exit_admin_panel(msg: Message, state: FSMContext):
    if not is_admin(msg.from_user.id):
        return
    await state.clear()
    ADMIN_SESSION.pop(msg.from_user.id, None)

    if msg.text == "🔙 Назад в панель":
        pending = load_pending_cases()
        await msg.answer(
            f"👨‍💼 *Админ-панель*\n\nКейсов на проверку: *{len(pending)}*",
            reply_markup=admin_main_keyboard(),
            parse_mode="Markdown",
        )
        return

    from app.bot.keyboards import main_menu_keyboard
    await msg.answer("Вы вышли из админ-панели.", reply_markup=main_menu_keyboard("ru"))


# stats
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

#control admins
@router.message(F.text == "👥 Управление админами")
async def manage_admins(msg: Message, state: FSMContext):
    if not is_admin(msg.from_user.id):
        return
    await state.clear()
    await msg.answer("👥 Управление админами",reply_markup=admins_keyboard(), parse_mode="Markdown")

# list of admins
@router.message(F.text == "📋 Список админов")
async def list_admins(msg: Message):
    if not is_admin(msg.from_user.id):
        return
    ids = load_admin_ids()

    lines = [f"👑 `{ROOT_ADMIN_ID}` — главный админ"]
    for admin_id in sorted(ids):
        if admin_id != ROOT_ADMIN_ID:
            lines.append(f"👤 `{admin_id}`")

    await msg.answer(
        "📋 Список администраторов:\n\n" + "\n".join(lines),
        reply_markup=admins_keyboard(),
        parse_mode="Markdown",
    )

# add admins
@router.message(F.text == "➕ Добавить админа")
async def add_admin_start(msg: Message, state: FSMContext):
    if not is_admin(msg.from_user.id):
        return

    await state.clear()
    await msg.answer(
        "➕ *Добавление нового администратора*\n\n"
        "Отправьте Telegram ID пользователя, которого хотите добавить.\n\n"
        "📌 *Как узнать Telegram ID:*\n"
        "1. Попросите пользователя написать боту @userinfobot\n"
        "2. Бот ответит его ID (только цифры)\n"
        "3. Скопируйте и отправьте сюда",
        reply_markup=cancel_keyboard(),
        parse_mode="Markdown",
    )
    await state.set_state(AdminReview.waiting_for_new_admin_id)

# cancel adding new admin
@router.message(AdminReview.waiting_for_new_admin_id, F.text == "❌ Отмена")
async def cancel_add_admin(msg: Message, state: FSMContext):
    await state.clear()
    await msg.answer("Отмененно", reply_markup=admins_keyboard())

# handel new admin id
@router.message(AdminReview.waiting_for_new_admin_id, F.text)
async def add_admin_confirm(msg: Message, state: FSMContext):
    if not is_admin(msg.from_user.id):
        return
    
    text = msg.text.strip()

    if not text.isdigit():
        await msg.answer("❌ Введите числовой Telegram ID(только цифры)")
        return
    
    new_id = int(text)
    ids = load_admin_ids()
    if new_id in ids:
        await msg.answer(f"⚠️ Пользователь `{new_id}` уже является админом", parse_mode="Markdown")

    else:
        ids.add(new_id)
        save_admin_ids(ids)
        await msg.answer(f"✅ Пользователь `{new_id}` добавлен как админ", parse_mode="Markdown")
    
    await state.clear()
    await msg.answer("Выберите действие:", reply_markup=admins_keyboard())


# remove admin
@router.message(F.text == "➖ Удалить админа")
async def remove_admin_start(msg: Message, state: FSMContext):
    if not is_admin(msg.from_user.id):
        return
    
    ids = load_admin_ids()

    removable = ids - {ROOT_ADMIN_ID}

    if not removable:
        await msg.answer("Нет дополнительных администраторов для удаления")
        return
    
    lines = "\n".join(f". `{i}`" for i in sorted(removable))
    await msg.answer(
        f"Отправьте ID админа для удаления:\n\n{lines}",
        reply_markup=cancel_keyboard(),
        parse_mode="Markdown",
    )
    await state.set_state(AdminReview.waiting_for_remove_admin_id)


# cancel removing admin
@router.message(AdminReview.waiting_for_remove_admin_id, F.text == "❌ Отмена")
async def cancel_remove_admin(msg: Message, state: FSMContext):
    await state.clear()
    await msg.answer("Отменено", reply_markup=admins_keyboard())


# remove admin confirm
@router.message(AdminReview.waiting_for_remove_admin_id, F.text)
async def remove_admin_confirm(msg: Message, state: FSMContext):
    
    if not is_admin(msg.from_user.id):
        return
    
    text = msg.text.strip()
    if not text.isdigit():
        await msg.answer("❌ Введите числовой Telegram ID")
        return
    
    remove_id = int(text)
    if remove_id == ROOT_ADMIN_ID:
        await msg.answer("⛔ Нельзя удалить главного администратора")
        state.clear()
        return
    ids = load_admin_ids()
    if remove_id not in ids:
        await msg.answer(f"⚠️ Пользователь `{remove_id}` не найден в списке", parse_mode="Markdown")
    else:
        ids.discard(remove_id)
        save_admin_ids(ids)
        await msg.answer(f"✅ Пользователь `{remove_id}` удалён из админов", parse_mode="Markdown")
    
    await state.clear()
    await msg.answer("Выберите действие:", reply_markup=admins_keyboard())



# case review

@router.message(F.text.in_(["📋 Кейсы на проверку", "📋 Все кейсы"]))
async def start_review(msg: Message, state: FSMContext):
    if not is_admin(msg.from_user.id):
        return
    cases = load_pending_cases()
    if not cases:
        await msg.answer("✅ Все кейсы проверены, очередь пуста.", reply_markup=admin_main_keyboard())
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
    try:
        await msg.answer(text, reply_markup=review_action_keyboard(), parse_mode="HTML")
    except Exception as e:
        # fallback: send without formatting if HTML still fails
        plain = (
            f"Кейс {index + 1}/{len(cases)}\n"
            f"ID: {case.get('case_id', '—')}\n"
            f"Вопрос: {case.get('question', '—')}\n"
            f"Ответ бота: {case.get('bot_answer', '—')[:300]}\n"
            f"Причина: {case.get('reason', '—')}"
        )
        await msg.answer(plain, reply_markup=review_action_keyboard())

########

@router.message(F.text == "✅ Написать ответ")
async def approve_start(msg: Message, state: FSMContext):
    if not is_admin(msg.from_user.id):
        return
    session = ADMIN_SESSION.get(msg.from_user.id)
    if not session:
        await msg.answer("Сначала откройте кейсы: «📋 Кейсы на проверку»")
        return
    case = session["cases"][session["index"]]
    is_image_case = case.get("reason") == "image_unrecognized"
    is_sync_critical = case.get("reason") == "sync_mismatch_critical"
    if is_image_case:
        hint = (
            "\n\n📷 <i>Это фото, которое бот не смог распознать. "
            "Опишите что на нём и дайте ответ — это попадёт в базу знаний.</i>"
        )
    elif is_sync_critical:
        hint = (
            "\n\n🚨 <b>КРИТИЧНО:</b> <i>Расхождение статусов между Faktura и Солик. "
            "Проверьте документ вручную. Ответ должен содержать: "
            "что было сделано для устранения расхождения.</i>"
        )
    else:
        hint = ""
    await msg.answer(
        f"✏️ <b>Напишите правильный ответ</b> для вопроса:\n\n"
        f"<i>{html.escape(case.get('question', ''))}</i>{hint}",
        reply_markup=cancel_keyboard(),
        parse_mode="HTML",
    )
    await state.set_state(AdminReview.waiting_for_answer)



# cancel_approve выполнял логику одобрения вместо отмены
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