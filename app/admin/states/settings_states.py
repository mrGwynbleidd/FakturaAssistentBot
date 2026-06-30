#FSM states for admin management (add / remove admin)

from aiogram.fsm.state import State, StatesGroup


class SettingsStates(StatesGroup):
    waiting_for_new_admin_id = State()
    waiting_for_remove_admin_id = State()
