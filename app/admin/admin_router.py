#assembles all admin sub-routers into a single admin_router for registration in main.py
#router order is critical — stats and review_cases must come before FSM routers
#used in main.py to register all admin functionality

#import libs
from aiogram import Router

#import all admin sub-routers
from app.admin.handlers.main_menu import router as main_menu_router
from app.admin.handlers.knowledge_create import router as knowledge_create_router
from app.admin.handlers.incidents_create import router as incidents_create_router
from app.admin.handlers.incidents_manage import router as incidents_manage_router
from app.admin.handlers.review_cases import router as review_cases_router
from app.admin.handlers.stats import router as stats_router
from app.admin.handlers.read_only import router as read_only_router


admin_router = Router(name="admin_router")

#stats and review_cases must be registered FIRST (before FSM routers)
#FSM handlers intercept ALL text in their state — if stats/review_cases come after,
#button presses inside an active FSM state will never reach the correct handler
admin_router.include_router(main_menu_router)
admin_router.include_router(stats_router)          #before FSM routers
admin_router.include_router(review_cases_router)   #view handler before FSM handlers
admin_router.include_router(knowledge_create_router)
admin_router.include_router(incidents_create_router)
admin_router.include_router(incidents_manage_router)
admin_router.include_router(read_only_router)
