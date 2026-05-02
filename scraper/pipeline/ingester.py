"""Ingester: takes ScraperResult objects and writes them to the database."""
from __future__ import annotations

import logging
from dataclasses import dataclass

from slugify import slugify
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from scrapers.base import ScrapedCourse, ScrapedVideo, ScraperResult

logger = logging.getLogger(__name__)


@dataclass
class IngestStats:
    universities_created: int = 0
    departments_created: int = 0
    subjects_created: int = 0
    courses_created: int = 0
    courses_updated: int = 0
    videos_created: int = 0


class DataIngester:
    """Persists scraped data to the database."""

    def __init__(self, db: AsyncSession, youtube_api_key: str = ""):
        self.db = db
        self.youtube_api_key = youtube_api_key
        self._uni_cache: dict[str, object] = {}
        self._dept_cache: dict[str, object] = {}
        self._subj_cache: dict[str, object] = {}

    async def ingest(
        self, result: ScraperResult, enrich_youtube: bool = True
    ) -> IngestStats:
        """Write all courses (and optionally their YouTube videos) to the DB."""
        # Import here to avoid circular import at module level
        from sqlalchemy.dialects.postgresql import insert as pg_insert

        stats = IngestStats()

        for course_data in result.courses:
            try:
                await self._ingest_course(course_data, stats)
            except Exception as exc:
                logger.error(
                    "Failed to ingest course '%s': %s", course_data.title, exc
                )

        await self.db.commit()

        # Enrich with YouTube data if API key is available
        if enrich_youtube and self.youtube_api_key and result.videos:
            stats.videos_created += await self._ingest_videos(result.videos)

        return stats

    async def _ingest_course(self, data: ScrapedCourse, stats: IngestStats) -> None:
        from app.models.university import University
        from app.models.department import Department
        from app.models.course import Course, CourseLevel, CourseSubject
        from app.models.subject import Subject

        # ── University ─────────────────────────────────────────────────────────
        uni_slug = data.university_slug or slugify(data.university_name)
        if uni_slug not in self._uni_cache:
            result = await self.db.execute(
                select(University).where(University.slug == uni_slug)
            )
            uni = result.scalar_one_or_none()
            if uni is None:
                uni = University(
                    name=data.university_name,
                    slug=uni_slug,
                    source_key=data.source_key,
                )
                self.db.add(uni)
                await self.db.flush()
                stats.universities_created += 1
            self._uni_cache[uni_slug] = uni
        uni = self._uni_cache[uni_slug]

        # ── Department ─────────────────────────────────────────────────────────
        dept = None
        if data.department_name:
            dept_key = f"{uni_slug}::{data.department_name}"
            if dept_key not in self._dept_cache:
                dept_slug = slugify(f"{data.department_name} {uni_slug}")
                result = await self.db.execute(
                    select(Department).where(Department.slug == dept_slug)
                )
                dept = result.scalar_one_or_none()
                if dept is None:
                    dept = Department(
                        university_id=uni.id,
                        name=data.department_name,
                        slug=dept_slug,
                    )
                    self.db.add(dept)
                    await self.db.flush()
                    stats.departments_created += 1
                self._dept_cache[dept_key] = dept
            dept = self._dept_cache[dept_key]

        # ── Subjects ───────────────────────────────────────────────────────────
        subject_ids: list = []
        for subj_name in data.subjects:
            if not subj_name:
                continue
            subj_slug = slugify(subj_name)
            if subj_slug not in self._subj_cache:
                result = await self.db.execute(
                    select(Subject).where(Subject.slug == subj_slug)
                )
                subj = result.scalar_one_or_none()
                if subj is None:
                    subj = Subject(name=subj_name, slug=subj_slug)
                    self.db.add(subj)
                    await self.db.flush()
                    stats.subjects_created += 1
                self._subj_cache[subj_slug] = subj
            subject_ids.append(self._subj_cache[subj_slug].id)

        # ── Course ─────────────────────────────────────────────────────────────
        result = await self.db.execute(
            select(Course).where(Course.slug == data.slug)
        )
        course = result.scalar_one_or_none()

        level_map = {
            "undergraduate": CourseLevel.undergraduate,
            "graduate": CourseLevel.graduate,
            "professional": CourseLevel.professional,
        }
        level = level_map.get(data.level, CourseLevel.other)

        if course is None:
            course = Course(
                university_id=uni.id,
                department_id=dept.id if dept else None,
                course_number=data.course_number,
                title=data.title,
                slug=data.slug,
                description=data.description,
                level=level,
                source_url=data.source_url,
                source_key=data.source_key,
                thumbnail_url=data.thumbnail_url,
                instructor=data.instructor,
                year=data.year,
                semester=data.semester,
                has_video_lectures=data.has_video_lectures,
                has_lecture_notes=data.has_lecture_notes,
                has_exams=data.has_exams,
                lecture_notes_url=data.lecture_notes_url,
                exams_url=data.exams_url,
                youtube_playlist_id=data.youtube_playlist_id,
            )
            self.db.add(course)
            await self.db.flush()
            stats.courses_created += 1
        else:
            # Update mutable fields
            course.youtube_playlist_id = course.youtube_playlist_id or data.youtube_playlist_id
            course.has_video_lectures = course.has_video_lectures or data.has_video_lectures
            course.has_lecture_notes = course.has_lecture_notes or data.has_lecture_notes
            course.has_exams = course.has_exams or data.has_exams
            stats.courses_updated += 1

        # ── Course-Subject links ────────────────────────────────────────────────
        for sid in subject_ids:
            exists = await self.db.execute(
                select(CourseSubject).where(
                    CourseSubject.course_id == course.id,
                    CourseSubject.subject_id == sid,
                )
            )
            if exists.scalar_one_or_none() is None:
                self.db.add(CourseSubject(course_id=course.id, subject_id=sid))

    async def _ingest_videos(
        self, videos_map: dict[str, list[ScrapedVideo]]
    ) -> int:
        from app.models.course import Course
        from app.models.video import Video

        count = 0
        for source_url, videos in videos_map.items():
            result = await self.db.execute(
                select(Course).where(Course.source_url == source_url)
            )
            course = result.scalar_one_or_none()
            if course is None:
                continue

            for sv in videos:
                exists = await self.db.execute(
                    select(Video).where(
                        Video.course_id == course.id,
                        Video.youtube_id == sv.youtube_id,
                    )
                )
                if exists.scalar_one_or_none() is None:
                    vid = Video(
                        course_id=course.id,
                        youtube_id=sv.youtube_id,
                        title=sv.title,
                        description=sv.description,
                        thumbnail_url=sv.thumbnail_url,
                        duration_seconds=sv.duration_seconds,
                        view_count=sv.view_count,
                        order=sv.order,
                    )
                    self.db.add(vid)
                    count += 1

            # Update course total_videos
            course.total_videos = len(videos)
            course.total_duration_seconds = sum(
                v.duration_seconds or 0 for v in videos
            )

        await self.db.commit()
        return count
