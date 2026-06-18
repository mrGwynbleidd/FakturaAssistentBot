from aiogram.fsm.state import StatesGroup, State

#bad answers from bot

class ReviewCasesStates(StatesGroup):
    
    waiting_for_case_id = State()
    waiting_for_admin_answer = State()
    waiting_for_confirmation = State()