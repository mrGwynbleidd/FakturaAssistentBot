
from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from app.admin.services.admin_access import is_admin, get_admin_language
from app.admin.services.knowledge_service import save_admin_knowledge
from app.admin.texts import get_admin_text
from app.admin.keyboards.main import admin_cancel_keyboard, admin_confirm_keyboard
from app.admin.keyboards.knowledge import knowledge_category_keyboard, knowledge_after_save_keyboard
from app.admin.states.knowledge_states import AddknowledgeStates

router = Router(name="admin_knowledge_create")

def text_values(key: str) -> list[str]:

    values = [
        get_admin_text(key, "ru"),
        get_admin_text(key, "uz"),
        get_admin_text(key, "en"),
        key,
    ]

    aliases = {
        "btn_add_qa": [
            "add_qa",
            "btn_add_qa",
            "➕ Добавить Q/A",
        ],
        "btn_cancel": [
            "cancel",
            "btn_cancel",
            "❌ Отмена",
        ],
        "btn_confirm": [
            "confirm",
            "btn_confirm",
            "✅ Подтвердить",
        ],
    }

    values.extend(aliases.get(key, []))

    return list(set(values))


def is_cancel_text(text: str | None) -> bool:
    return text in text_values("btn_cancel")

@router.message(F.text.in_(text_values("btn_add_qa")))
async def start_add_qa(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id if message.from_user else None):
        return

    language = get_admin_language(message.from_user.id if message.from_user else None)

    await state.clear()
    await state.set_state(AddknowledgeStates.waiting_for_question)

    await message.answer(
        f"{get_admin_text('add_qa_start', language)}\n\n"
        f"{get_admin_text('enter_question', language)}",
        reply_markup=admin_cancel_keyboard(language),
    )


@router.message(AddknowledgeStates.waiting_for_question)
async def add_qa_question(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id if message.from_user else None):
        return

    language = get_admin_language(message.from_user.id if message.from_user else None)

    if is_cancel_text(message.text):
        await state.clear()
        await message.answer(
            get_admin_text("qa_cancelled", language),
            reply_markup=knowledge_after_save_keyboard(language),
        )
        return

    question = (message.text or "").strip()

    if not question:
        await message.answer(get_admin_text("enter_question", language))
        return
    
    await state.update_data(question=question)
    await state.set_state(AddknowledgeStates.waiting_for_answer)

    await message.answer(
        get_admin_text("enter_answer", language),
        reply_markup=admin_cancel_keyboard(language),
    )



@router.message(AddknowledgeStates.waiting_for_answer)
async def add_qa_answer(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id if message.from_user else None):
        return

    language = get_admin_language(message.from_user.id if message.from_user else None)

    if is_cancel_text(message.text):
        await state.clear()
        await message.answer(
            get_admin_text("qa_cancelled", language),
            reply_markup=knowledge_after_save_keyboard(language),
        )
        return
    
    answer = (message.text or "").strip()

    if not answer:
        await message.answer(get_admin_text("enter_answer", language))
        return
    
    await state.update_data(answer=answer)
    await state.set_state(AddknowledgeStates.waiting_for_category)

    await message.answer(
        get_admin_text("enter_category", language),
        reply_markup=knowledge_category_keyboard(language),
    )


@router.message(AddknowledgeStates.waiting_for_category)
async def add_qa_category(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id if message.from_user else None):
        return

    language = get_admin_language(message.from_user.id if message.from_user else None)

    if is_cancel_text(message.text):
        await state.clear()
        await message.answer(
            get_admin_text("qa_cancelled", language),
            reply_markup=knowledge_after_save_keyboard(language),
        )
        return

    category = (message.text or "general").strip() or "general"

    await state.update_data(category=category)
    await state.set_state(AddknowledgeStates.waiting_for_tags)

    await message.answer(get_admin_text("enter_tags", language), reply_markup=admin_cancel_keyboard(language),)


@router.message(AddknowledgeStates.waiting_for_tags)
async def add_qa_tags(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id if message.from_user else None):
        return

    language = get_admin_language(message.from_user.id if message.from_user else None)

    if is_cancel_text(message.text):
        await state.clear()
        await message.answer(
            get_admin_text("qa_cancelled", language),
            reply_markup=knowledge_after_save_keyboard(language),
        )
        return

    tags = (message.text or "").strip()
    await state.update_data(tags = tags)

    data = await state.get_data()

    preview = (
        f"{get_admin_text('qa_preview_title', language)}\n\n"
        f"Вопрос:\n{data.get('question', '')}\n\n"
        f"Ответ:\n{data.get('answer', '')}\n\n"
        f"Категория: {data.get('category', 'general')}\n"
        f"Теги: {data.get('tags', '')}"
    )

    await state.set_state(AddknowledgeStates.waiting_for_confirmation)

    await message.answer(preview, reply_markup=admin_confirm_keyboard(language),)


@router.message(AddknowledgeStates.waiting_for_confirmation)
async def add_qa_confirm(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id if message.from_user else None):
        return

    admin_id = message.from_user.id if message.from_user else None
    language = get_admin_language(admin_id)

    if is_cancel_text(message.text):
        await state.clear()
        await message.answer(
            get_admin_text("qa_cancelled", language),
            reply_markup=knowledge_after_save_keyboard(language)
        )
        return
    
    if message.text not in text_values("btn_confirm"):
        await message.answer(
            get_admin_text("btn_confirm", language),
            reply_markup=admin_confirm_keyboard(language),
        )
        return
    
    data = await state.get_data()

    knowledge_id = save_admin_knowledge(
        question=data.get("question", ""),
        answer=data.get("answer", ""),
        language=language,
        category=data.get("category", "general"),
        tags=data.get("tags", ""),
        created_by=admin_id or "",
        status="approved",
    )

    await state.clear()

    await message.answer(
        f"{get_admin_text('qa_saved', language)}\nID: {knowledge_id}",
        reply_markup=knowledge_after_save_keyboard(language),
    )

    
