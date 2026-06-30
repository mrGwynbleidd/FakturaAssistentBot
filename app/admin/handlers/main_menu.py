#admin main menu handler — /admin command, back/cancel/exit button routing
#sends the admin keyboard menu, clears FSM state, handles universal cancel
#used as entry point to the admin panel

from aiogram import Router, F
from aiogram.filters import Command, Filter, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, ReplyKeyboardRemove

from app.admin.services.admin_access import is_admin, get_admin_language
from app.admin.texts import get_admin_text
from app.admin.keyboards.main import admin_main_keyboard
from app.admin.keyboards.settings import settings_keyboard
from app.admin.states.settings_states import SettingsStates

router = Router(name="admin_main_menu")


#returns the button text in all three supported languages for filter matching
def admin_button_values(key: str) -> list[str]:
    return [
        get_admin_text(key, "ru"),
        get_admin_text(key, "uz"),
        get_admin_text(key, "en"),
    ]


#filter-level admin check — returns False for non-admins so message falls through to next router
#using a Filter class instead of checking inside handler prevents message from being "swallowed"
class IsAdminFilter(Filter):
    async def __call__(self, message: Message) -> bool:
        return is_admin(message.from_user.id if message.from_user else None)


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


#handles "back" button — returns to main admin menu
#excluded during settings FSM states so the settings handler can catch it and go back to settings keyboard
@router.message(
    F.text.in_(admin_button_values("btn_back")),
    ~StateFilter(
        SettingsStates.waiting_for_new_admin_id,
        SettingsStates.waiting_for_remove_admin_id,
    ),
)
async def admin_back_button(message: Message, state: FSMContext):
    await send_admin_menu(message, state)


#universal cancel for admins — catches cancel button in any FSM state including after restart
#IsAdminFilter in the decorator ensures non-admins pass through to their own cancel handlers
#StateFilter exclusions ensure this doesn't intercept user-level or settings-level FSM flows
_CANCEL_BUTTON_TEXTS = admin_button_values("btn_cancel") + [
    "❌ Отменить",
]

from app.bot.sync_roaming_states import UserSyncRoamingStates

@router.message(
    F.text.in_(_CANCEL_BUTTON_TEXTS),
    IsAdminFilter(),
    ~StateFilter(
        UserSyncRoamingStates.waiting_for_roaming_id,
        UserSyncRoamingStates.waiting_for_inn,
        UserSyncRoamingStates.waiting_for_model_type,
        SettingsStates.waiting_for_new_admin_id,
        SettingsStates.waiting_for_remove_admin_id,
    ),
)
async def admin_cancel_any_state(message: Message, state: FSMContext):
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

@router.message(F.text.in_(_EXIT_BUTTON_TEXTS), IsAdminFilter())
async def admin_exit_button(message: Message, state: FSMContext):
    await state.clear()
    language = get_admin_language(message.from_user.id if message.from_user else None)
    await message.answer(
        get_admin_text("operation_cancelled", language),
        reply_markup=ReplyKeyboardRemove(),
    )


#settings button handler — opens settings/admin management keyboard
@router.message(F.text.in_(admin_button_values("btn_settings")), IsAdminFilter())
async def admin_settings_button(message: Message):
    language = get_admin_language(message.from_user.id if message.from_user else None)
    await message.answer(
        get_admin_text("settings_title", language),
        reply_markup=settings_keyboard(language),
    )


#manage admins button — direct shortcut from main keyboard to settings/admin management keyboard
@router.message(F.text.in_(admin_button_values("btn_manage_admins")), IsAdminFilter())
async def admin_manage_admins_button(message: Message):
    language = get_admin_language(message.from_user.id if message.from_user else None)
    await message.answer(
        get_admin_text("settings_title", language),
        reply_markup=settings_keyboard(language),
    )
