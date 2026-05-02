from app.schemas.base import OCWBase, TimestampMixin
from app.schemas.university import UniversityRead, UniversityCreate, UniversityUpdate, UniversityList
from app.schemas.subject import SubjectRead, SubjectCreate, SubjectUpdate, SubjectList
from app.schemas.course import (
    CourseRead,
    CourseSummary,
    CourseCreate,
    CourseUpdate,
    CourseList,
    CourseFilters,
    VideoSummary,
)
from app.schemas.video import VideoRead, VideoCreate, VideoUpdate, VideoList
from app.schemas.admin import (
    ScraperJobCreate,
    ScraperJobRead,
    ScraperJobList,
    TokenResponse,
    LoginRequest,
    StatsResponse,
)

__all__ = [
    "OCWBase",
    "TimestampMixin",
    "UniversityRead",
    "UniversityCreate",
    "UniversityUpdate",
    "UniversityList",
    "SubjectRead",
    "SubjectCreate",
    "SubjectUpdate",
    "SubjectList",
    "CourseRead",
    "CourseSummary",
    "CourseCreate",
    "CourseUpdate",
    "CourseList",
    "CourseFilters",
    "VideoSummary",
    "VideoRead",
    "VideoCreate",
    "VideoUpdate",
    "VideoList",
    "ScraperJobCreate",
    "ScraperJobRead",
    "ScraperJobList",
    "TokenResponse",
    "LoginRequest",
    "StatsResponse",
]
