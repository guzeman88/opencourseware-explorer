"""SQLAlchemy models – all imported here so Alembic can discover them."""

from app.models.base import Base
from app.models.university import University
from app.models.department import Department
from app.models.subject import Subject
from app.models.course import Course, CourseSubject
from app.models.video import Video
from app.models.scraper_job import ScraperJob
from app.models.user import User
from app.models.roadmap import Roadmap, RoadmapEntry
from app.models.watch_history import UserWatchHistory

__all__ = [
    "Base",
    "University",
    "Department",
    "Subject",
    "Course",
    "CourseSubject",
    "Video",
    "ScraperJob",
    "User",
    "Roadmap",
    "RoadmapEntry",
    "UserWatchHistory",
]
