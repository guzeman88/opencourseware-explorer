# Preservation Inventory

This inventory defines what must remain intact while The Commons is repaired.
It contains no credentials or personally identifiable user data.

## Essential Public Features

- Home discovery rows, featured courses, continue watching, and responsive navigation
- Course catalog filters, sorting, pagination, and list/grid presentation
- Search results and course navigation
- Subject index, subject detail results, counts, and relevance ordering
- University index and university course listings
- Course detail playback, lecture selection, source/material links, and back navigation
- Roadmap index, roadmap detail, ordering, and linked courses
- Library save/remove behavior and empty/loading/error states
- Installable PWA manifest, icons, splash assets, home-screen launch, and mobile menu
- Responsive desktop and mobile visual treatment

## Essential Admin Features

- Admin authentication and protected routing
- Dashboard statistics
- Course audit and editing
- Pending-review workflow
- University and source views
- Scraper-job status
- Publish/unpublish behavior

## Essential API Features

- Public courses, featured courses, search, universities, subjects, and roadmaps
- User registration, login, profile, library, and watch history
- Admin authentication, statistics, courses, universities, and scraper jobs
- Relative `/api/v1` Netlify proxy behavior and Render API availability

## Persistent Data

| Table | Purpose | Preservation rule |
|---|---|---|
| `universities` | Source institutions and channels | Never delete during cleanup |
| `departments` | Institution departments | Preserve links to courses |
| `courses` | Master source and catalog records | Hide uncertain records; do not delete |
| `videos` | Lecture metadata and YouTube IDs | Recover/reconcile before excluding |
| `subjects` | Subject taxonomy | Preserve identifiers and hierarchy |
| `course_subjects` | Current subject membership | Export before any rewrite |
| `course_subject_relevance` | Scored subject evidence | Version and preserve before rebuilding |
| `roadmaps` | Learning roadmap definitions | Preserve order and university ownership |
| `roadmap_entries` | Ordered roadmap courses | Preserve positions and nullable links |
| `users` | User accounts | Never expose, reset, or delete |
| `user_library_courses` | Saved courses | Never lose relationships |
| `user_watch_history` | Continue-watching state | Never lose relationships or indexes |
| `scraper_jobs` | Ingestion history | Preserve for auditability |

## Derived and Denormalized Data

- `courses.has_video_lectures`
- `courses.total_videos`
- `courses.total_duration_seconds`
- `courses.view_count`
- `courses.is_published`
- `courses.search_vector`
- subject counts and relevance ordering
- frontend cached API data and PWA caches

Derived data may be recalculated only from preserved source records, with
before/after comparison and rollback evidence.

## Deployment and Configuration

- GitHub repository and `main` history
- Netlify production site and deploy history
- Render API service and environment variables
- Neon PostgreSQL database and restore points
- YouTube Data API credentials and quota
- Sentry and Google Analytics integrations
