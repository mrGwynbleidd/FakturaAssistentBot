from aiogram.fsm.state import StatesGroup, State


class ReviewCasesStates(StatesGroup):
    browsing = State()               # showing a single case, waiting for button press
    waiting_for_admin_answer = State()  # admin pressed approve, now typing the answer
