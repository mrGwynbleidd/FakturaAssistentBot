
from app.admin.handlers.main_menu import router as main_menu_router
from app.admin.handlers.knowledge_create import router as knowledge_create_router
from app.admin.handlers.incidents_create import router as incidents_create_router
from app.admin.handlers.incidents_manage import router as incidents_manage_router
from app.admin.handlers.review_cases import router as review_cases_router
from app.admin.handlers.stats import router as stats_router

__all__ = [
    "main_menu_router",
    "knowledge_create_router",
    "incidents_create_router",
    "incidents_manage_router",
    "review_cases_router",
    "stats_router",
]
