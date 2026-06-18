
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, ReplyKeyboardRemove

from app.admin.services.admin_access import is_admin, get_admin_language
from app.admin.texts import get_admin_text
from app.admin.keyboards.main import admin_main_keyboard

router = Router(name="admin_main_menu")

def admin_button_values(key: str) -> list[str]:
    return [
        get_admin_text(key, "ru"),
        get_admin_text(key, "uz"),
        get_admin_text(key, "en"),
    ]

async def send_admin_menu(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id if message.from_user else None):
        await message.answer(get_admin_text("access_denied", "ru"))
        return

    if state:
        await state.clear()

    language = get_admin_language(message.from_user.id if message.from_user else None)

    await message.answer(
        f"{get_admin_text('admin_menu_title', language)}\n"
        f"{get_admin_text('admin_menu_description', language)}",
        reply_markup=admin_main_keyboard(language),
    )


@router.message(Command("admin"))
async def admin_command(message: Message, state: FSMContext):
    await send_admin_menu(message, state)


@router.message(F.text.in_(admin_button_values("btn_back")))
async def admin_back_button(message: Message, state: FSMContext):
    await send_admin_menu(message, state)

@router.message(F.text.in_(admin_button_values("btn_exit")))
async def admin_exit_button(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id if message.from_user else None):
        return

    await state.clear()
    language = get_admin_language(message.from_user.id if message.from_user else None)

    await message.answer(
        get_admin_text("operation_cancelled", language),
        reply_markup=ReplyKeyboardRemove(),
    )


@router.message(F.text.in_(admin_button_values("btn_settings")))
async def admin_settings_button(message: Message):
    if not is_admin(message.from_user.id if message.from_user else None):
        return

    language = get_admin_language(message.from_user.id if message.from_user else None)

    await message.answer(
        "⚙️ Настройки админ-панели пока в разработке.\n\n"
        "Сейчас доступны: Q/A, временные проблемы, review cases и статистика",
        reply_markup=admin_main_keyboard(language),
    )