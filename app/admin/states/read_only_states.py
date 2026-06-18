
from aiogram.fsm.state import State, StatesGroup

class ReadOnlyStates(StatesGroup):
    waiting_for_chat_id_to_add = State()
    waiting_for_chat_id_to_remove = State()
