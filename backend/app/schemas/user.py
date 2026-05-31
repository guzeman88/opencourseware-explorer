import uuid
from datetime import datetime

from pydantic import BaseModel, EmailStr, field_validator
from app.schemas.course import CourseSummary


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str

    @field_validator("password")
    @classmethod
    def password_length(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        return v


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserRead(BaseModel):
    id: uuid.UUID
    email: str
    is_admin: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class LibraryCourseId(BaseModel):
    course_id: uuid.UUID


class LibraryStatusResponse(BaseModel):
    saved: bool


class WatchHistoryCreate(BaseModel):
    course_id: uuid.UUID
    video_index: int = 0


class WatchHistoryEntry(BaseModel):
    course_id: uuid.UUID
    video_index: int
    watched_at: datetime

    model_config = {"from_attributes": True}


class WatchHistoryWithCourse(BaseModel):
    course: CourseSummary
    video_index: int
    watched_at: datetime

    model_config = {"from_attributes": True}
