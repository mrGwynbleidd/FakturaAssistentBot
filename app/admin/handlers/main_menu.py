#admin main menu handler — /admin command, back/cancel/exit button routing
#sends the admin keyboard menu, clears FSM state, handles universal cancel
#used as entry point to the admin panel

from aiogram import Router, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, ReplyKeyboardRemove

from app.admin.services.admin_access import is_admin, get_admin_language
from app.admin.texts import get_admin_text
from app.admin.keyboards.main import admin_main_keyboard

router = Router(name="admin_main_menu")

#returns the button text in all three supported languages for filter matching
def admin_button_values(key: str) -> list[str]:
    return [
        get_admin_text(key, "ru"),
        get_admin_text(key, "uz"),
        get_admin_text(key, "en"),
    ]


#sends the admin main menu, clears any active FSM state
#called by /admin command and all back-button handlers
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


#handles /admin command — shows admin menu
@router.message(Command("admin"))
async def admin_command(message: Message, state: FSMContext):
    await send_admin_menu(message, state)


#handles "back" button presses — returns to main admin menu
@router.message(F.text.in_(admin_button_values("btn_back")))
async def admin_back_button(message: Message, state: FSMContext):
    await send_admin_menu(message, state)


#universal cancel handler — catches cancel button in ANY FSM state including after restart
#clears FSM state and shows main menu even if cancel was sent mid-flow
_CANCEL_BUTTON_TEXTS = admin_button_values("btn_cancel") + [
    "❌ Отменить",
]

@router.message(F.text.in_(_CANCEL_BUTTON_TEXTS))
async def admin_cancel_any_state(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id if message.from_user else None):
        return

    current_state = await state.get_state()
    # Only handle if NOT already in a FSM state — FSM handlers manage their own cancel
    if current_state is not None:
        # Let the FSM state handler deal with it (return = don't consume)
        # NOTE: we can't actually "pass through" in aiogram once filter matched,
        # so we replicate the cancel behavior here universally
        pass

    await state.clear()
    language = get_admin_language(message.from_user.id if message.from_user else None)
    await message.answer(
        get_admin_text("operation_cancelled", language),
        reply_markup=admin_main_keyboard(language),
    )


#exit button handler — removes keyboard and exits admin panel entirely
_EXIT_BUTTON_TEXTS = admin_button_values("btn_exit") + [
    "\U0001f6aa Выйти из панели",
]

@router.message(F.text.in_(_EXIT_BUTTON_TEXTS))
async def admin_exit_button(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id if message.from_user else None):
        return

    await state.clear()
    language = get_admin_language(message.from_user.id if message.from_user else None)

    await message.answer(
        get_admin_text("operation_cancelled", language),
        reply_markup=ReplyKeyboardRemove(),
    )


#settings button handler — placeholder that shows admin menu with description
@router.message(F.text.in_(admin_button_values("btn_settings")))
async def admin_settings_button(message: Message):
    if not is_admin(message.from_user.id if message.from_user else None):
        return

    language = get_admin_language(message.from_user.id if message.from_user else None)

    await message.answer(
        get_admin_text("admin_menu_title", language) + "\n\n"
        "Q/A, временные проблемы, review cases и статистика",
        reply_markup=admin_main_keyboard(language),
    )
