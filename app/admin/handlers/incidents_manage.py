
from aiogram import Router, F
from aiogram.filters import Command, CommandObject
from aiogram.types import Message

from app.admin.services.admin_access import is_admin, get_admin_language
from app.admin.services.incident_service import list_active_incidents, disable_incident
from app.admin.texts import get_admin_text
from app.admin.keyboards.incidents import incident_manage_keyboard

router = Router(name="admin_incidents_manage")

def text_values(key: str) -> list[str]:
    
    values = [
        get_admin_text(key, "ru"),
        get_admin_text(key, "uz"),
        get_admin_text(key, "en"),
        key,
    ]

    aliases = {
        "btn_active_incidents": [
            "btn_active_incident",
            "btn_active_incidents",
            "active_incident",
            "active_incidents",
            "📌 Активные проблемы",
        ],
    }

    values.extend(aliases.get(key, []))

    return list(set(values))



def format_incident_row(row: dict, index: int) -> str:
    return (
        f"{index}. {row.get('title', '')}\n"
        f"ID: {row.get('incident_id', '')}\n"
        f"Статус: {row.get('status', '')}\n"
        f"Ключевые слова: {row.get('keywords', '')}\n"
        f"До: {row.get('end_at', '') or 'не указано'}\n"
        f"Ответ: {row.get('answer', '')[:300]}"
    )


@router.message(F.text.in_(text_values("btn_active_incidents")))
async def show_active_incidents(message: Message):
    if not is_admin(message.from_user.id if message.from_user else None):
        return
    
    language = get_admin_language(message.from_user.id if message.from_user else None)
    incidents = list_active_incidents(language=language)

    if not incidents:
        await message.answer(
            get_admin_text("no_active_incidents", language),
            reply_markup=incident_manage_keyboard(language),
        )
        return
    
    parts = [get_admin_text("active_incident_title", language)]

    for index, incident in enumerate(incidents[:10], start=1):
        parts.append(format_incident_row(incident, index))

    
    parts.append(
        "\nЧтобы отключить проблему, отправьте команду:\n"
        "/disable_incident incident_id"
    )

    await message.answer(
        "\n\n".join(parts),
        reply_markup=incident_manage_keyboard(language),
    )


@router.message(Command("disable_incident"))
async def disable_incident_command(message: Message, command:CommandObject):
    if not is_admin(message.from_user.id if message.from_user else None):
        return

    admin_id = message.from_user.id if message.from_user else None
    language = get_admin_language(admin_id)

    incident_id = (command.args or "").strip()

    if not incident_id:
        await message.answer("Укажите ID: /disable_incident inc_...")
        return
    
    ok = disable_incident(
        incident_id=incident_id,
        admin_id=admin_id,
    )

    if not ok:
        await message.answer(get_admin_text("incident_not_found", language))
        return
    
    await message.answer(
        get_admin_text("incident_disabled", language),
        reply_markup=incident_manage_keyboard(language),
    )

    