# The Commons — Operations & Developer Runbook

This is the single source of truth for building, running, deploying, and maintaining The Commons. If something is not in here, add it.

All repair and modernization work must follow the preservation-first gates in
**[COMPREHENSIVE_REPAIR_ROADMAP.md](COMPREHENSIVE_REPAIR_ROADMAP.md)**. Essential
features, data, and rollback procedures are tracked under `preservation/`.

---

## Table of Contents

1. [Production Infrastructure](#1-production-infrastructure)
2. [Where All Data Lives](#2-where-all-data-lives)
3. [Data Protection & Backup](#3-data-protection--backup)
4. [Environment Variables Reference](#4-environment-variables-reference)
5. [Local Development Setup](#5-local-development-setup)
6. [Backend (FastAPI)](#6-backend-fastapi)
7. [Web Frontend (Next.js)](#7-web-frontend-nextjs)
8. [Mobile App (Expo)](#8-mobile-app-expo)
9. [Scraper Pipeline](#9-scraper-pipeline)
10. [Database & Migrations](#10-database--migrations)
11. [Deployment](#11-deployment)
12. [How to Ship Changes](#12-how-to-ship-changes)
13. [Known Bugs & Technical Debt](#13-known-bugs--technical-debt)
14. [Monitoring & Alerting](#14-monitoring--alerting)
15. [Common Runbook Tasks](#15-common-runbook-tasks)

---

## 1. Production Infrastructure

```
Users
  │
  ▼
Netlify CDN  ──────────────────────────────────────────────────────────────
  │  https://opencourseware-explorer.netlify.app                          │
  │  Next.js 14 App Router (Netlify Next.js plugin)                       │
  │  ISR: homepage revalidates every 300s                                 │
  │                                                                       │
  │  Built from: opencourseware/web/                                      │
  │  Triggered by: every push to main branch                              │
  │                                                                       │
  ▼
Render (free tier web service)  ────────────────────────────────────────────
  │  https://opencourseware-api.onrender.com                              │
  │  FastAPI + uvicorn (Docker)                                           │
  │  Spins down after 15 min inactivity (free tier cold start ~30s)       │
  │                                                                       │
  │  Built from: opencourseware/backend/ (Dockerfile)                     │
  │  Triggered by: manual deploy or auto-deploy on push                   │
  │                                                                       │
  ▼
Neon (serverless PostgreSQL)  ──────────────────────────────────────────────
     https://console.neon.tech
     Project: ep-blue-leaf-aq4lk4jf
     Branch: main
     Database: neondb
     Region: us-east-1
     9,726 courses · 15,425 course_subjects tags
```

### Service Accounts

| Service | Login | Where credentials are |
|---------|-------|-----------------------|
| Netlify | guzeman88@yahoo.com | Netlify dashboard |
| Render | guzeman88@yahoo.com | Render dashboard |
| Neon | guzeman88@yahoo.com | Neon console |
| GitHub | guzeman88 | https://github.com/guzeman88/opencourseware-explorer |
| Sentry | guzeman88@yahoo.com | sentry.io |

---

## 2. Where All Data Lives

> **Read this section carefully before running any destructive commands.**

### Primary Database — Neon PostgreSQL

**This is the only persistent store for all user and course data.**

| What | Where |
|------|-------|
| All 9,726 courses | `courses` table |
| All 15,425 subject tags | `course_subjects` table |
| All universities | `universities` table |
| All subjects taxonomy | `subjects` table |
| User accounts | `users` table |
| User bookmarks / Library | `user_library_courses` table |
| Video metadata | `videos` table |
| Learning roadmaps | `roadmaps` + `roadmap_entries` tables |

Connection string (stored in Render env vars and in `.env` locally):
```
postgresql+asyncpg://neondb_owner:<password>@ep-blue-leaf-aq4lk4jf.c-8.us-east-1.aws.neon.tech/neondb?sslmode=require
```

> **⚠️ The Neon database is the single source of truth. There is no secondary replica. If data is deleted it must be re-scraped or restored from a manual backup. User accounts and bookmarks cannot be recovered from scraping.**

### Scraper Source Files (local only)

| File | What it contains | Risk if lost |
|------|-----------------|--------------|
| `MIT Course List Master - MIT Course List Master.csv` | 2,573 MIT course records | High — required to reload MIT courses |
| `course-availability-report.csv` | Audit of source availability | Low |
| `opencourseware/scraper/discovered_channels.json` | YouTube channel IDs discovered during scraping | Medium — can be re-discovered |
| `opencourseware/scraper/channel_scrape_progress.json` | Checkpoint file for long scrape runs | Low — only used mid-run |

### No Local Database

There is no local PostgreSQL instance that matters. All data is on Neon. Running scrapers locally writes directly to Neon via `DATABASE_URL`.

### Git Repository

All source code is at `github.com/guzeman88/opencourseware-explorer`. The working directory `C:\Users\Jorge DeGuzeman\Desktop\code-projects\Courses\opencourseware\` is a clone of that repo.

---

## 3. Data Protection & Backup

### How to Avoid Losing Data

**Rule 1: Never run `DROP TABLE`, `TRUNCATE`, or `DELETE FROM` on Neon without a backup.**

**Rule 2: Never run `tag_courses.py` with `RESET_TAGS=1` without first verifying the tagging logic is correct.** This wipes and rebuilds all 15,425 subject tags.

**Rule 3: Never run `alembic downgrade` on the production database without a backup.**

**Rule 4: User accounts and bookmarks cannot be re-created from scraping. Treat the `users` and `user_library_courses` tables as irreplaceable.**

### Manual Database Backup (Neon)

Neon does not auto-backup on the free tier. Take a manual backup before any risky operation.

**Option A — pg_dump (recommended)**

```powershell
# From the workspace root — requires pg_dump in PATH
# Windows: install PostgreSQL tools from https://www.postgresql.org/download/windows/

$env:DATABASE_URL = "postgresql://neondb_owner:<password>@ep-blue-leaf-aq4lk4jf.c-8.us-east-1.aws.neon.tech/neondb?sslmode=require"

pg_dump $env:DATABASE_URL `
  --format=custom `
  --file="backup_$(Get-Date -Format 'yyyyMMdd_HHmm').dump"
```

**Option B — Neon branching (zero-copy, instant)**

In the Neon console (console.neon.tech):
1. Select the `neondb` database
2. Click **Branches → Create branch**
3. Name it `backup-YYYY-MM-DD`
4. This creates an instant point-in-time copy with no storage overhead until it diverges

Branches can be deleted after a risky migration is confirmed successful.

### Restoring from Backup

```powershell
# Restore from a pg_dump file
pg_restore `
  --dbname="postgresql://neondb_owner:<password>@ep-blue-leaf-aq4lk4jf.c-8.us-east-1.aws.neon.tech/neondb?sslmode=require" `
  --clean `
  --if-exists `
  backup_20260530_1200.dump
```

### What Can Be Rebuilt vs. What Cannot

| Data | Recoverable without backup? | How |
|------|:--:|-----|
| Course metadata (title, URL, description) | ✅ Yes | Re-run scrapers |
| YouTube video data | ✅ Yes | Re-run `scrape_all_playlists_api.py` |
| Subject tags | ✅ Yes | Re-run `tag_courses.py` |
| Thumbnails | ✅ Yes | Re-run `backfill_thumbnails.py` |
| User accounts | ❌ No | Must restore from backup |
| User bookmarks (Library) | ❌ No | Must restore from backup |
| Roadmap data | ⚠️ Partial | Re-run `load_roadmaps.py` but custom edits are lost |

### Credential Rotation

If any of the following credentials are compromised, rotate them immediately:

| Credential | How to rotate |
|------------|--------------|
| Neon DB password | Neon console → Settings → Connection Details → Reset password. Update `DATABASE_URL` in Render env vars. |
| `SECRET_KEY` (JWT signing) | Generate new: `openssl rand -hex 32`. Update in Render env vars. **All existing user sessions will be invalidated.** |
| YouTube API key | GCP console → Credentials → Regenerate. Update `YOUTUBE_API_KEY` in local `.env`. |
| Render admin password | Set `ADMIN_PASSWORD` env var in Render dashboard, redeploy. |

> **⚠️ Security note:** The YouTube API key and Neon connection string have appeared in PowerShell terminal history. If this machine is shared or the history is synced anywhere, rotate both.

---

## 4. Environment Variables Reference

### Backend — set in Render dashboard

| Variable | Required | Description |
|----------|:--------:|-------------|
| `DATABASE_URL` | ✅ | `postgresql+asyncpg://neondb_owner:<pw>@ep-blue-leaf-aq4lk4jf.c-8.us-east-1.aws.neon.tech/neondb?sslmode=require` |
| `SECRET_KEY` | ✅ | JWT signing secret. Generate: `openssl rand -hex 32`. **Never use the default.** |
| `ADMIN_EMAIL` | ✅ | Admin dashboard login email |
| `ADMIN_PASSWORD` | ✅ | Admin dashboard login password (bcrypt-hashed at startup) |
| `CORS_ORIGINS` | ✅ | Comma-separated or JSON array: `https://opencourseware-explorer.netlify.app` |
| `ENVIRONMENT` | ✅ | Set to `production` |
| `YOUTUBE_API_KEY` | ⚠️ | Required only for scraper enrichment. Not needed for the API to run. |
| `SENTRY_DSN` | ⚠️ | Sentry error reporting. Leave empty to disable. |
| `DEBUG` | — | `false` in production |

### Web Frontend — set in Netlify dashboard

| Variable | Required | Description |
|----------|:--------:|-------------|
| `API_UPSTREAM` | ✅ | `https://opencourseware-api.onrender.com` for SSR and the `/api/v1` proxy |
| `NEXT_PUBLIC_API_URL` | ✅ | Leave empty so browser requests use relative `/api/v1` and Netlify can proxy/cache them |
| `NEXT_PUBLIC_GA_MEASUREMENT_ID` | ⚠️ | Google Analytics 4 Measurement ID (`G-XXXXXXXXXX`). Code is deployed; just needs this value. |
| `NEXT_PUBLIC_SENTRY_DSN` | ⚠️ | Sentry DSN for client-side error reporting |
| `SENTRY_AUTH_TOKEN` | ⚠️ | Sentry source map upload token |

### Scraper — set locally in PowerShell before running

```powershell
$env:DATABASE_URL  = "postgresql://neondb_owner:<pw>@ep-blue-leaf-aq4lk4jf.c-8.us-east-1.aws.neon.tech/neondb?sslmode=require"
$env:YOUTUBE_API_KEY = "<your-key>"
```

### Local Development — `web/.env.local`

```
NEXT_PUBLIC_API_URL=
```

Leave `NEXT_PUBLIC_API_URL` empty unless you are intentionally running a local backend. Empty means browser requests use relative `/api/v1`, which goes through the Next.js proxy route and falls back to the live Render backend. Setting this to a dead local port makes the app appear blank or skeleton-only after the splash.

---

## 5. Local Development Setup

### Prerequisites

- Python 3.12+
- Node.js 20+
- The `.venv` virtual environment at `C:\Users\Jorge DeGuzeman\Desktop\code-projects\Courses\.venv\`

### Backend (native, no Docker)

```powershell
cd "C:\Users\Jorge DeGuzeman\Desktop\code-projects\Courses\opencourseware\backend"

python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt -r requirements-dev.txt

# Point at Neon (or a local Postgres)
$env:DATABASE_URL = "postgresql+asyncpg://..."
$env:SECRET_KEY   = "dev-only-secret"

uvicorn app.main:app --reload --port 8000
# → http://localhost:8000/docs
```

### Web Frontend (native)

```powershell
cd "C:\Users\Jorge DeGuzeman\Desktop\code-projects\Courses\opencourseware\web"

npm install

# Create web/.env.local:
# NEXT_PUBLIC_API_URL=http://localhost:8000

npm run dev
# → http://localhost:3000
```

### Virtual Environment (shared, workspace-level)

A shared `.venv` exists at the workspace root and is used for all scraper scripts:

```
C:\Users\Jorge DeGuzeman\Desktop\code-projects\Courses\.venv\Scripts\python.exe
```

Activate it in any terminal:
```powershell
.venv\Scripts\Activate.ps1
```

All scraper one-liners in this document assume this venv is active.

---

## 6. Backend (FastAPI)

**Location:** `opencourseware/backend/`  
**Language:** Python 3.12  
**Framework:** FastAPI 0.111 + SQLAlchemy 2.0 async  
**Database driver:** asyncpg  
**Auth:** JWT via `python-jose` + `pbkdf2_sha256`  
**Deployed:** Render — `https://opencourseware-api.onrender.com`

### API Routers

All routes mount at `/api/v1/`.

| File | Prefix | Notes |
|------|--------|-------|
| `routers/courses.py` | `/courses` | List, filter, detail, featured, view-count increment. Has 60s in-process TTL cache. |
| `routers/universities.py` | `/universities` | List + per-university course listing |
| `routers/subjects.py` | `/subjects` | Subject taxonomy (flat + hierarchical) |
| `routers/search.py` | `/search` | `ilike` full-text search on course title |
| `routers/roadmaps.py` | `/roadmaps` | Learning roadmaps |
| `routers/users.py` | `/users` | Auth (register/login) + Library CRUD — **must be mounted in `main.py`** (see §13) |
| `routers/admin.py` | `/admin` | Stats, pending review, publish toggle — JWT-protected |

### Auth Flow

1. `POST /api/v1/users/register` or `POST /api/v1/users/login` → returns `{ access_token }` (JWT)
2. Client stores token in `localStorage` under key `ocw_user_token`
3. Protected endpoints require `Authorization: Bearer <token>`
4. Tokens expire after 7 days (`access_token_expire_minutes = 60 * 24 * 7`)
5. On 401, the frontend clears `ocw_user_token` from localStorage

### Startup Behaviour

On startup (`lifespan` in `main.py`):
1. In `development` mode: auto-creates all tables via `Base.metadata.create_all`
2. In `production` mode: **skips table creation** — use Alembic migrations
3. Bootstraps the admin user from `ADMIN_EMAIL` / `ADMIN_PASSWORD` env vars (non-fatal if DB is temporarily unavailable)

### Rate Limiting

- Auth endpoints (`/users/register`, `/users/login`): **10 requests/minute per IP** via `slowapi`
- All other endpoints: no rate limit currently set

---

## 7. Web Frontend (Next.js)

**Location:** `opencourseware/web/`  
**Framework:** Next.js 14.2.35 (App Router)  
**Deployed:** Netlify — `https://opencourseware-explorer.netlify.app`  
**Build trigger:** every push to `main`

### Pages

| Route | File | Render type | Description |
|-------|------|-------------|-------------|
| `/` | `app/page.tsx` | Server + ISR (300s) | Homepage: hero + ~70 subject course rows |
| `/courses` | `app/courses/page.tsx` | Client | Paginated course browser with filters |
| `/courses/[id]` | `app/courses/[id]/` | Client | Course detail + video list |
| `/universities` | `app/universities/` | Client | University grid |
| `/universities/[slug]` | `app/universities/[slug]/` | Client | University course listing |
| `/subjects` | `app/subjects/` | Client | Subject browser |
| `/search` | `app/search/page.tsx` | Client | Full-text search |
| `/browse` | `app/browse/page.tsx` | Client | Table-style course browser by university/subject |
| `/library` | `app/library/page.tsx` | Client | User's bookmarked courses (auth required) |
| `/roadmaps` | `app/roadmaps/page.tsx` | Client | Learning roadmaps grouped by field |
| `/admin` | `app/admin/` | Client (JWT) | Admin dashboard |

### Provider Hierarchy

```
layout.tsx
  └── <QueryProvider>            ← TanStack Query client
        └── <AppShell>
              └── <AuthProvider>        ← JWT token, user state, rehydration
                    └── <AuthModalProvider>  ← openAuthModal() context
                          ├── <Navbar>
                          ├── {children}
                          ├── <footer>
                          ├── <PwaRegister>
                          └── <AuthModal> (conditional)
```

### Auth Token Storage

- User token: `localStorage["ocw_user_token"]` — managed by `AuthProvider`
- Admin token: `localStorage["ocw_token"]` — managed by the admin login page
- The 401 response interceptor in `api.ts` clears **both** keys on auth failure

### ISR / Caching Strategy

- Homepage: `revalidate = 300` (5 min). Netlify CDN serves cached HTML.
- Course rows below the fold: lazy-fetched client-side via `IntersectionObserver` (300px preload margin)
- All client fetches: TanStack Query with `staleTime = 30,000ms`
- Backend courses list: in-process 60s TTL cache keyed on all filter parameters

### Security Headers (set in `next.config.js`)

- `X-Content-Type-Options: nosniff`
- `X-Frame-Options: DENY`
- `X-XSS-Protection: 1; mode=block`
- `Referrer-Policy: strict-origin-when-cross-origin`
- `Permissions-Policy: camera=(), microphone=(), geolocation=()`

---

## 8. Mobile App (Expo)

**Location:** `opencourseware/mobile/`  
**Status: NOT DEPLOYED.** This is an early prototype. Do not point users to it.

**Known bugs before it can be shipped:**
- Thumbnail calculation uses `course.university_slug` instead of `course.thumbnail_url` — all thumbnails are broken
- No auth system (no login, no Library, no token management)
- No Sentry / crash reporting
- `eas.json` and `app.json` are not configured for production (no bundle ID, store IDs, etc.)

---

## 9. Scraper Pipeline

**Location:** `opencourseware/scraper/`  
**Language:** Python 3.12  
**Runs:** manually, on-demand, from a local machine pointing at Neon

All scraper commands require `DATABASE_URL` set in the shell.

### Canonical One-liner (PowerShell)

```powershell
cd "C:\Users\Jorge DeGuzeman\Desktop\code-projects\Courses"
$env:DATABASE_URL  = "postgresql://neondb_owner:<pw>@ep-blue-leaf-aq4lk4jf.c-8.us-east-1.aws.neon.tech/neondb?sslmode=require"
$env:YOUTUBE_API_KEY = "<key>"
```

### Active Scripts (used regularly)

| Script | What it does | When to run |
|--------|-------------|-------------|
| `tag_courses.py` | Keyword-tags all courses into subjects | After a bulk data load, or to fix tag coverage. Use `$env:RESET_TAGS="1"` to wipe and rebuild all tags. |
| `scrape_all_playlists_api.py` | Fetches YouTube playlist metadata (video count, duration, thumbnail) for all courses with a `youtube_playlist_id` | When new courses are added or video data is stale |
| `backfill_thumbnails.py` | Fills in missing thumbnails from YouTube API or OG image fallback | After bulk load if thumbnails are missing |
| `load_roadmaps.py` | Loads learning roadmap data into the `roadmaps` table | When updating roadmap content |
| `load_mit_csv.py` / `load_csv_fast.py` | Loads MIT OCW courses from the CSV file | When re-seeding MIT data |
| `scrape_nptel_full.py` | Scrapes NPTEL courses | When updating NPTEL content |
| `scrape_harvard_full.py` | Scrapes Harvard courses | When updating Harvard content |
| `fix_labels_and_publish.py` | Sets `is_published=True` for courses meeting quality criteria | After bulk load |

### Tag System

`tag_courses.py` maps keyword rules → subject slugs. Current stats: **15,425 tags across 9,726 courses (73.8% coverage)**.

To reset and rebuild all tags:
```powershell
$env:RESET_TAGS = "1"
.venv\Scripts\python.exe opencourseware\scraper\tag_courses.py
```

> **⚠️ Warning:** `RESET_TAGS=1` deletes ALL rows in `course_subjects` before rebuilding. Do not run this if you have made manual tag edits you want to keep.

### One-off Fix Scripts (`_` prefix)

Scripts prefixed with `_` are one-off audits and fixes applied during development (e.g., `_fix_schema.py`, `_audit_tags.py`). They are safe to ignore but should not be deleted — they document the data cleaning history.

---

## 10. Database & Migrations

**Engine:** PostgreSQL (Neon serverless)  
**ORM:** SQLAlchemy 2.0 async  
**Migrations:** Alembic (in `backend/`)

### Running Migrations

```powershell
cd "C:\Users\Jorge DeGuzeman\Desktop\code-projects\Courses\opencourseware\backend"
$env:DATABASE_URL = "postgresql+asyncpg://neondb_owner:<pw>@ep-blue-leaf-aq4lk4jf.c-8.us-east-1.aws.neon.tech/neondb?sslmode=require"

alembic upgrade head
```

**Always take a Neon branch backup (§3) before running migrations in production.**

### Creating a Migration

After changing a model in `backend/app/models/`:

```powershell
cd backend
alembic revision --autogenerate -m "brief description of change"
# Review the generated file in migrations/versions/
alembic upgrade head
```

### Alembic Connection

`alembic.ini` has a hardcoded fallback URL for local dev. In production, the `DATABASE_URL` env var is used. Always verify `DATABASE_URL` is set correctly before running migrations.

### Schema Overview

```
universities    ← source institutions
departments     ← optional sub-groupings within a university
courses         ← 9,726 rows; core entity
  └── videos    ← YouTube video records per course
  └── course_subjects  ← many-to-many: courses ↔ subjects (15,425 rows)
subjects        ← subject taxonomy (~150 rows)
users           ← user accounts (email + hashed password)
user_library_courses  ← user bookmarks (user_id, course_id)
roadmaps        ← learning roadmap definitions
roadmap_entries ← ordered course list within each roadmap
```

---

## 11. Deployment

### Web → Netlify

Every push to `main` should trigger the Netlify build hook in `.github/workflows/deploy.yml`. Do not assume that is enough for phone testing: after user-facing web changes, verify the production URL or run an explicit Netlify deploy and report the URL.

| Property | Value |
|----------|-------|
| Site URL | `https://opencourseware-explorer.netlify.app` |
| Site name | `opencourseware-explorer` |
| Site ID | `54de50b1-3845-47d0-b667-d0a955e3e724` |
| Build command | `npm run build` (run from `web/`) |
| Publish dir | `web/.next` |
| Plugin | `@netlify/plugin-nextjs` |
| Env vars | Set in Netlify dashboard → Site settings → Environment variables |

**Normal deploy path for a web change:**
```powershell
cd "C:\Users\Jorge DeGuzeman\Desktop\code-projects\Courses\opencourseware"
git fetch --all --prune
git status --short --branch
npm --prefix web run build
git add -- web/src/... netlify.toml
git commit -m "describe change"
git push origin main
```

Then confirm the Netlify build hook completed, or deploy explicitly for immediate phone testing:

```powershell
netlify deploy --prod --site 54de50b1-3845-47d0-b667-d0a955e3e724 --build
```

After deploy, verify with a cache-busted request:

```powershell
Invoke-WebRequest "https://opencourseware-explorer.netlify.app/?verify=$(Get-Date -UFormat %s)" -UseBasicParsing
```

For mobile UI changes, also open the Netlify URL on a phone and verify the interaction there. Report the production URL, unique deploy URL, deploy ID, commit hash, and what was verified.

**Local Netlify state:**

`.netlify/` is intentionally ignored because it is local CLI state. If `netlify status` says the folder is not linked, do not guess the site. Use the site ID above, or relink explicitly:

```powershell
netlify link --id 54de50b1-3845-47d0-b667-d0a955e3e724
```

### Backend → Render (manual or auto)

| Property | Value |
|----------|-------|
| Service URL | `https://opencourseware-api.onrender.com` |
| Build source | `backend/Dockerfile` |
| Config file | `backend/render.yaml` |
| Env vars | Set in Render dashboard → Environment |
| Cold start | ~30s on free tier (first request after 15 min idle) |

**To deploy a backend change:**
```powershell
git add backend/
git commit -m "describe change"
git push origin main
# Trigger a manual deploy in Render dashboard, OR enable auto-deploy from main
```

**⚠️ `render.yaml` currently contains plaintext credentials** (`ADMIN_PASSWORD`, a legacy `DATABASE_URL`). These values are overridden by Render dashboard env vars at runtime, but the file should be cleaned up — replace them with `sync: false` placeholders.

### Deployment Checklist (before any production push)

- [ ] `npm run build` passes locally in `web/`
- [ ] No TypeScript errors (`tsc --noEmit` in `web/`)
- [ ] Backend `SECRET_KEY` is set to a non-default value in Render
- [ ] `CORS_ORIGINS` includes `https://opencourseware-explorer.netlify.app` in Render
- [ ] Neon branch backup taken if the change includes a DB migration

---

## 12. How to Ship Changes

### Git Workflow

The repo is at `opencourseware/` (a clone of `github.com/guzeman88/opencourseware-explorer`). All git commands run from inside that directory.

```powershell
cd "C:\Users\Jorge DeGuzeman\Desktop\code-projects\Courses\opencourseware"

git status
git add <files>
git commit -m "type: short description"
git push origin main
```

**Commit message format:** `type: description`  
Types: `feat` (new feature), `fix` (bug fix), `chore` (maintenance), `docs` (documentation)

> PowerShell tip: paths with parentheses must be quoted:
> `git add "mobile/app/(tabs)/index.tsx"`

### Changing the Web UI

| What to change | Where |
|----------------|-------|
| Homepage course rows | `web/src/app/page.tsx` — add/remove `<CourseRow>` components |
| Shared components | `web/src/components/` |
| API calls (client) | `web/src/lib/api.ts` + hooks in `web/src/hooks/` |
| Auth logic | `web/src/providers/auth-provider.tsx` |
| Global styles | `web/src/app/globals.css` |
| ISR revalidation period | `revalidate = 300` in page files (seconds) |

### Changing the Backend

1. Edit the router in `backend/app/routers/`
2. Add/modify Pydantic schemas in `backend/app/schemas/`
3. If a DB model changed, create an Alembic migration (§10)
4. Push to `main` → manually trigger redeploy in Render dashboard

### Adding a New Subject Row to the Homepage

In `web/src/app/page.tsx`:
```tsx
<CourseRow
  title="Your Subject Title"
  queryKey="unique-key-no-spaces"
  fetchType="subject"
  subjectSlug="slug-from-subjects-table"
/>
```

The `subjectSlug` must match a slug in the `subjects` table. Verify with:
```powershell
$env:DATABASE_URL = "..."
.venv\Scripts\python.exe -c "
import psycopg, os
with psycopg.connect(os.environ['DATABASE_URL'].replace('+asyncpg', '')) as conn:
    rows = conn.execute('SELECT slug FROM subjects ORDER BY slug').fetchall()
    for r in rows: print(r[0])
"
```

---

## 13. Known Bugs & Technical Debt

These are confirmed bugs that need fixing. Prioritised highest to lowest.

### 🔴 Critical

**1. `users.py` router is not mounted in `main.py`**  
File: `backend/app/main.py`  
The `users` router (`/users/register`, `/users/login`, `/users/me`, `/users/me/library`) is never imported or registered. All auth and Library endpoints return 404 in production.  
Fix: add `from app.routers import users` and `app.include_router(users.router, prefix="/api/v1")` to `main.py`.

**2. Admin login token/cookie mismatch**  
File: `web/src/middleware.ts` + `web/src/app/admin/login/`  
The edge middleware checks for an `ocw_session` **httpOnly cookie**, but the admin login page stores the token in `localStorage["ocw_token"]`. The cookie is never set, so the middleware redirects every request — the admin panel is permanently inaccessible.  
Fix: either set a cookie on login response, or change the middleware to accept the Bearer token via an `Authorization` header.

**3. `render.yaml` contains plaintext credentials**  
File: `backend/render.yaml`  
`ADMIN_PASSWORD` and a legacy `DATABASE_URL` are committed in plaintext. While Render dashboard env vars override these at runtime, they should be removed from the file.  
Fix: replace with `sync: false` entries and set values only in Render dashboard.

### 🟡 High

**4. No Sentry on the backend**  
`sentry-sdk` is not in `requirements.txt`. Backend crashes on Render are invisible.  
Fix: add `sentry-sdk[fastapi]>=2.0` to `requirements.txt`, initialise in `run.py` or `main.py`.

**5. No silent token refresh**  
When a JWT expires, the 401 interceptor clears localStorage and the user is silently signed out mid-session. There is no refresh endpoint.  
Fix: add `POST /api/v1/users/refresh` to the backend returning a new token; call it from the 401 interceptor before clearing state.

**6. Browse page loads all courses on category expand**  
File: `web/src/app/browse/page.tsx`  
When a university or subject section is expanded, all courses for that section are fetched with no pagination. With large universities (e.g. NPTEL ~3,200 courses) this causes a large query and slow render.  
Fix: add cursor-based pagination with a "load more" button.

**7. `render.yaml` / `SECRET_KEY` default**  
If `SECRET_KEY` is not set in Render dashboard env vars, the default `"change-me-in-production"` is used, making all JWTs forgeable.  
Fix: verify `SECRET_KEY` is set in Render. `openssl rand -hex 32` to generate.

### 🟢 Medium

**8. Full-text search uses `ilike`**  
`list_courses` does `Course.title.ilike('%query%')` — a sequential scan with no index. Will degrade as course count grows.  
Fix: add a `pg_trgm` GIN index on `courses.title`.

**9. No Privacy Policy page**  
Required before collecting analytics data (GA4) or accepting user registrations (GDPR/CCPA).  
Fix: add a `/privacy` route with a basic privacy policy.

**10. No per-route `loading.tsx`**  
Only the root `loading.tsx` exists. `/courses`, `/library`, `/roadmaps` have no loading skeleton.  
Fix: add `loading.tsx` per route for smoother transitions.

---

## 14. Monitoring & Alerting

### Sentry (Frontend)

Sentry is configured in:
- `web/src/sentry.client.config.ts` — client-side
- `web/src/instrumentation.ts` — server/edge
- `web/src/app/error.tsx` — catches render errors and calls `captureException`

To activate: set `NEXT_PUBLIC_SENTRY_DSN` in Netlify dashboard.

### Sentry (Backend)

Not yet configured. See bug #4 in §13.

### Uptime Monitoring

No uptime monitor is currently configured. The backend health endpoint is:
```
GET https://opencourseware-api.onrender.com/health
→ {"status": "ok", "version": "1.0.0"}
```

Set up a free monitor at [uptimerobot.com](https://uptimerobot.com) pointing at this URL. Configure an email alert for downtime.

### Google Analytics 4

Code is deployed. Activate by setting `NEXT_PUBLIC_GA_MEASUREMENT_ID=G-XXXXXXXXXX` in Netlify dashboard. The GA4 property must be created first at [analytics.google.com](https://analytics.google.com).

Tracked automatically:
- Every page view (via `usePathname` + `useSearchParams`)

Custom events available via `trackEvent()` in `web/src/components/google-analytics.tsx`:
```ts
trackEvent({ action: "bookmark_added", category: "library", label: courseId });
```

---

## 15. Common Runbook Tasks

### Re-tag all courses (subject taxonomy rebuild)

```powershell
cd "C:\Users\Jorge DeGuzeman\Desktop\code-projects\Courses"
$env:DATABASE_URL = "postgresql://..."
$env:RESET_TAGS = "1"
.venv\Scripts\python.exe opencourseware\scraper\tag_courses.py
# Expected: ~15,000 tags inserted across ~9,726 courses
```

### Backfill missing thumbnails

```powershell
$env:DATABASE_URL = "postgresql://..."
$env:YOUTUBE_API_KEY = "..."
.venv\Scripts\python.exe opencourseware\scraper\backfill_thumbnails.py
```

### Refresh YouTube video metadata

```powershell
$env:DATABASE_URL = "postgresql://..."
$env:YOUTUBE_API_KEY = "..."
.venv\Scripts\python.exe opencourseware\scraper\scrape_all_playlists_api.py
```

### Check database health (course counts by source)

```powershell
$env:DATABASE_URL = "postgresql://..."
.venv\Scripts\python.exe opencourseware\scraper\count_catalogue.py
```

### Manually connect to the Neon database

```powershell
# Requires psql in PATH (install PostgreSQL tools)
psql "postgresql://neondb_owner:<pw>@ep-blue-leaf-aq4lk4jf.c-8.us-east-1.aws.neon.tech/neondb?sslmode=require"

# Useful queries:
# \dt                                          list all tables
# SELECT COUNT(*) FROM courses;               total courses
# SELECT COUNT(*) FROM courses WHERE is_published; published courses
# SELECT source_key, COUNT(*) FROM courses GROUP BY source_key ORDER BY COUNT(*) DESC;
# SELECT COUNT(*) FROM users;                 total users
# SELECT COUNT(*) FROM user_library_courses;  total bookmarks
```

### Force a Netlify redeploy (without a code change)

Preferred for traceability: use the explicit CLI deploy command from the current pushed commit, then verify the production URL. Dashboard fallback: Netlify dashboard → Deploys → Trigger deploy → Deploy site.

### Force a Render redeploy (without a code change)

In the Render dashboard → Manual Deploy → Deploy latest commit.

### Rotate the JWT secret key

1. Generate new key: `openssl rand -hex 32`
2. Set `SECRET_KEY` in Render dashboard → Environment
3. Trigger a Render redeploy
4. **All existing user sessions are immediately invalidated.** Users will need to sign in again.
