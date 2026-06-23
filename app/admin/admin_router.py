#collect all routers

#import libs
from aiogram import Router

#import functions, keyboards, routers
from app.admin.handlers.main_menu import router as main_menu_router
from app.admin.handlers.knowledge_create import router as knowledge_create_router
from app.admin.handlers.incidents_create import router as incidents_create_router
from app.admin.handlers.incidents_manage import router as incidents_manage_router
from app.admin.handlers.review_cases import router as review_cases_router
from app.admin.handlers.stats import router as stats_router
from app.admin.handlers.read_only import router as read_only_router



admin_router = Router(name="admin_router")

# ВАЖНО: stats и review_cases должны быть ПЕРВЫМИ (до FSM-роутеров).
# FSM-хэндлеры (approve_case_answer, waiting_for_answer и т.д.) перехватывают
# ЛЮБОЙ текст в своём состоянии — если stats/review_cases зарегистрированы после,
# нажатие кнопки в активном FSM-состоянии никогда не дойдёт до нужного хэндлера.
admin_router.include_router(main_menu_router)
admin_router.include_router(stats_router)          # до FSM-роутеров
admin_router.include_router(review_cases_router)   # view-хэндлер до FSM-хэндлеров
admin_router.include_router(knowledge_create_router)
admin_router.include_router(incidents_create_router)
admin_router.include_router(incidents_manage_router)
admin_router.include_router(read_only_router)



