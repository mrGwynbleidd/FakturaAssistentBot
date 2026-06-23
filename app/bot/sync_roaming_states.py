
from aiogram.fsm.state import StatesGroup, State

class UserSyncRoamingStates(StatesGroup):
    waiting_for_roaming_id = State()
    waiting_for_inn = State()
    waiting_for_model_type = State()
