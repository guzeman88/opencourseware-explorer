from app.routers.courses import router as courses_router
from app.routers.universities import router as universities_router
from app.routers.subjects import router as subjects_router
from app.routers.search import router as search_router
from app.routers.admin import router as admin_router

__all__ = [
    "courses_router",
    "universities_router",
    "subjects_router",
    "search_router",
    "admin_router",
]
