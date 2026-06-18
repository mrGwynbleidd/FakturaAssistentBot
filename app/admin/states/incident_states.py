from aiogram.fsm.state import StatesGroup, State

#temp issues
class AddIncidentStates(StatesGroup):
    waiting_for_title = State()
    waiting_for_problem_text = State()
    waiting_for_keywords = State()
    waiting_for_answer = State()
    waiting_for_end_time = State()
    waiting_for_match_mode = State()
    waiting_for_confirmation = State()