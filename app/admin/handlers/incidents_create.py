
from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import Message


from app.admin.services.admin_access import is_admin, get_admin_language
from app.admin.services.incident_service import save_incident
from app.admin.texts import get_admin_text
from app.admin.keyboards.main import admin_cancel_keyboard, admin_confirm_keyboard
from app.admin.keyboards.incidents import (
    incident_match_mode,
    incident_after_save_keyboard,
)
from app.admin.states.incident_states import AddIncidentStates

router = Router(name="admin_incidents_create")

def text_values(key: str) -> list[str]:
    return [
        get_admin_text(key, "ru"),
        get_admin_text(key, "uz"),
        get_admin_text(key, "en"),
    ]


def is_cancel_text(text: str | None) -> bool:
    return text in text_values("btn_cancel")

@router.message(F.text.in_(text_values("btn_add_incident")))
async def start_add_incident(message: Message, state: FSMContext):

    if not is_admin(message.from_user.id if message.from_user else None):
        return
    
    language = get_admin_language(message.from_user.id if message.from_user else None)

    await state.clear()
    await state.set_state(AddIncidentStates.waiting_for_title)

    await message.answer(
        f"{get_admin_text('add_incident_start', language)}\n\n"
        f"{get_admin_text('enter_incident_title', language)}",
        reply_markup=admin_cancel_keyboard(language),
    )


@router.message(AddIncidentStates.waiting_for_title)
async def incident_title(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id if message.from_user else None):
        return
    
    language = get_admin_language(message.from_user.id if message.from_user else None)

    if is_cancel_text(message.text):
        await state.clear()
        await message.answer(
            get_admin_text("incident_cancelled", language),
            reply_markup=incident_after_save_keyboard(language),
        )
        return
    
    title = (message.text or "").strip()

    if not title:
        await message.answer(get_admin_text("enter_incident_title", language))
        return
    
    await state.update_data(title=title)
    await state.set_state(AddIncidentStates.waiting_for_problem_text)

    await message.answer(
        get_admin_text("enter_incident_problem", language),
        reply_markup=admin_cancel_keyboard(language),
    )


@router.message(AddIncidentStates.waiting_for_problem_text)
async def incident_problem_text(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id if message.from_user else None):
        return
    
    language = get_admin_language(message.from_user.id if message.from_user else None)

    if is_cancel_text(message.text):
        await state.clear()
        await message.answer(
            get_admin_text("incident_cancelled", language),
            reply_markup=incident_after_save_keyboard(language),
        )
        return
    
    problem_text = (message.text or "").strip()

    if not problem_text:
        await message.answer(get_admin_text("enter_inciddent_problem", language))
        return
    
    await state.update_data(problem_text=problem_text)
    await state.set_state(AddIncidentStates.waiting_for_keywords)

    await message.answer(
        get_admin_text("enter_incident_keywords", language),
        reply_markup=admin_cancel_keyboard(language),
    )


@router.message(AddIncidentStates.waiting_for_keywords)
async def incident_keywords(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id if message.from_user else None):
        return
    
    language = get_admin_language(message.from_user.id if message.from_user else None)

    if is_cancel_text(message.text):
        await state.clear()
        await message.answer(
            get_admin_text("incident_cancelled", language),
            reply_markup=incident_after_save_keyboard(language),
        )
        return
    
    keywords = (message.text or "").strip()

    if not keywords:
        await message.answer(get_admin_text("enter_inlacident_keywords", language))
        return
    
    await state.update_data(keywords=keywords)
    await state.set_state(AddIncidentStates.waiting_for_answer)

    await message.answer(
        get_admin_text("enter_incident_answer", language),
        reply_markup=admin_cancel_keyboard(language),
    )


@router.message(AddIncidentStates.waiting_for_answer)
async def incident_answer(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id if message.from_user else None):
        return
    
    language = get_admin_language(message.from_user.id if message.from_user else None)

    if is_cancel_text(message.text):
        await state.clear()
        await message.answer(
            get_admin_text("incident_cancelled", language),
            reply_markup=incident_after_save_keyboard(language),
        )

        return
    
    answer = (message.text or "").strip()

    if not answer:
        await message.answer(get_admin_text("enter_incident_answer", language))
        return
    
    await state.update_data(answer=answer)
    await state.set_state(AddIncidentStates.waiting_for_end_time)

    await message.answer(
        get_admin_text("enter_incident_end_time", language),
        reply_markup=admin_cancel_keyboard(language),
    )



@router.message(AddIncidentStates.waiting_for_end_time)
async def incident_end_time(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id if message.from_user else None):
        return
    
    language = get_admin_language(message.from_user.id if message.from_user else None)

    if is_cancel_text(message.text):
        await state.clear()
        await message.answer(
            get_admin_text("incident_cancelled", language),
            reply_markup=incident_after_save_keyboard(language),
        )
        return
    
    end_time = (message.text or "").strip()

    if end_time.lower() in {"none", "no", "-", "", "нет"}:
        end_time = ""

    await state.update_data(end_time=end_time)
    await state.set_state(AddIncidentStates.waiting_for_match_mode)

    await message.answer(
        "Выберите режим совпадения:\n"
        "contains — если вопрос содержит хотя бы одно ключевое слово.\n"
        "all_keywords — если вопрос содержит все ключевые слова.",
        reply_markup=incident_match_mode(language),
    )


@router.message(AddIncidentStates.waiting_for_match_mode)
async def incident_match_mode_handler(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id if message.from_user else None):
        return
    
    language = get_admin_language(message.from_user.id if message.from_user else None)

    if is_cancel_text(message.text):
        await state.clear()
        await message.answer(
            get_admin_text("incident_cancelled", language),
            reply_markup=incident_after_save_keyboard(language),
        )
        return
    
    match_mode = (message.text or "contains").strip()

    if match_mode not in {"contains", "all_keywords"}:
        match_mode = "contains"

    await state.update_data(match_mode=match_mode)

    data = await state.get_data()

    preview = (
        f"{get_admin_text('incident_preview_title', language)}\n\n"
        f"Название: {data.get('title', '')}\n"
        f"Проблема: {data.get('problem_text', '')}\n"
        f"Ключевые слова: {data.get('keywords', '')}\n"
        f"Режим: {data.get('match_mode', 'contains')}\n"
        f"Активна до: {data.get('end_at', '') or 'не указано'}\n\n"
        f"Ответ пользователям:\n{data.get('answer', '')}"        
    )

    await state.set_state(AddIncidentStates.waiting_for_confirmation)

    await message.answer(
        preview,
        reply_markup=admin_confirm_keyboard(language),
    )


@router.message(AddIncidentStates.waiting_for_confirmation)
async def incident_confirm(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id if message.from_user else None):
        return

    admin_id = message.from_user.id if message.from_user else None
    language = get_admin_language(admin_id)

    if is_cancel_text(message.text):
        await state.clear()
        await message.answer(
            get_admin_text("incident_cancelled", language),
            reply_markup=incident_after_save_keyboard(language),
        )
        return

    if message.text not in text_values("btn_confirm"):
        await message.answer(
            get_admin_text("btn_confirm", language),
            reply_markup=admin_confirm_keyboard(language),
        )
        return

    data = await state.get_data()

    incident_id = save_incident(
        title=data.get("title", ""),
        problem_text=data.get("problem_text", ""),
        answer=data.get("answer", ""),
        keywords=data.get("keywords", ""),
        language=language,
        match_mode=data.get("match_mode", "contains"),
        end_at=data.get("end_at", ""),
        created_by=admin_id or "",
        status="active",
    )

    await state.clear()

    await message.answer(
        f"{get_admin_text('incident_saved', language)} \nID: {incident_id}",
        reply_markup=incident_after_save_keyboard(language),
    )

    
