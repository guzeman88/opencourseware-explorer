from app.crud.courses import (
    get_course_by_id,
    get_course_by_slug,
    list_courses,
    create_course,
    update_course,
    delete_course,
    increment_view,
)
from app.crud.universities import (
    get_university_by_id,
    get_university_by_slug,
    list_universities,
    create_university,
    upsert_university,
    update_university,
    delete_university,
)
from app.crud.subjects import (
    get_subject_by_slug,
    list_subjects,
    get_or_create_subject,
    create_subject,
)

__all__ = [
    "get_course_by_id",
    "get_course_by_slug",
    "list_courses",
    "create_course",
    "update_course",
    "delete_course",
    "increment_view",
    "get_university_by_id",
    "get_university_by_slug",
    "list_universities",
    "create_university",
    "upsert_university",
    "update_university",
    "delete_university",
    "get_subject_by_slug",
    "list_subjects",
    "get_or_create_subject",
    "create_subject",
]
