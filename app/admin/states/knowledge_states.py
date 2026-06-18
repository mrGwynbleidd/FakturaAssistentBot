from aiogram.fsm.state import StatesGroup, State

class AddknowledgeStates(StatesGroup):
    waiting_for_question = State()
    waiting_for_answer = State()
    waiting_for_category = State()
    waiting_for_tags = State()
    waiting_for_confirmation = State()