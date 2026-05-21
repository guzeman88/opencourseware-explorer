# OCW Explorer — Operations & Developer Guide

Everything you need to build, run, change, and deploy this app.

---

## Table of Contents

1. [Repo Structure](#1-repo-structure)
2. [Architecture Overview](#2-architecture-overview)
3. [Environment Variables](#3-environment-variables)
4. [Local Development](#4-local-development)
5. [Backend (FastAPI)](#5-backend-fastapi)
6. [Web Frontend (Next.js)](#6-web-frontend-nextjs)
7. [Mobile App (Expo)](#7-mobile-app-expo)
8. [Scraper Pipeline](#8-scraper-pipeline)
9. [Database & Migrations](#9-database--migrations)
10. [Deployment](#10-deployment)
11. [Making and Shipping Changes](#11-making-and-shipping-changes)
12. [Testing](#12-testing)
13. [Monitoring & Error Tracking](#13-monitoring--error-tracking)
14. [Common Tasks](#14-common-tasks)

---

## 1. Repo Structure

```
opencourseware/                  ← git repo root (github.com/guzeman88/opencourseware-explorer)
├── backend/                     ← FastAPI REST API
│   ├── app/
│   │   ├── config.py            ← All settings (reads .env)
│   │   ├── main.py              ← App factory, middleware, lifespan hooks
│   │   ├── database.py          ← Async SQLAlchemy engine + session factory
│   │   ├── models/              ← SQLAlchemy ORM models
│   │   ├── schemas/             ← Pydantic request/response schemas
│   │   ├── crud/                ← DB query functions
│   │   ├── routers/             ← Route handlers (courses, universities, search, admin…)
│   │   └── services/            ← Auth (JWT + bcrypt), business logic
│   ├── migrations/              ← Alembic migration scripts
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── requirements-dev.txt
│   ├── railway.toml             ← Railway deployment config
│   └── render.yaml              ← Render deployment config
├── web/                         ← Next.js 14 frontend (PWA)
│   ├── src/app/                 ← Next.js App Router pages
│   │   ├── page.tsx             ← Homepage (ISR, server component)
│   │   ├── layout.tsx           ← App shell (QueryProvider, Sentry, PWA)
│   │   ├── courses/             ← Course detail page
│   │   ├── universities/        ← University listing + detail
│   │   ├── subjects/            ← Subject listing
│   │   ├── search/              ← Search page
│   │   ├── browse/              ← Browse/filter page
│   │   ├── library/             ← Saved courses (client-only)
│   │   ├── roadmaps/            ← Learning roadmaps
│   │   └── admin/               ← Admin dashboard
│   ├── src/components/          ← Reusable UI components
│   ├── src/hooks/               ← Custom React hooks
│   ├── src/lib/                 ← API client, utilities
│   ├── src/providers/           ← QueryProvider, ThemeProvider
│   ├── src/types/               ← Shared TypeScript types
│   ├── next.config.js           ← Next.js + Sentry + bundle analyser config
│   ├── Dockerfile               ← Multi-stage Docker build
│   └── package.json
├── mobile/                      ← Expo React Native app
│   ├── app/
│   │   ├── (tabs)/              ← Tab-based navigation root
│   │   │   ├── index.tsx        ← Browse/Home tab
│   │   │   ├── search.tsx       ← Search tab
│   │   │   ├── universities.tsx ← Universities tab
│   │   │   └── saved.tsx        ← Saved courses tab
│   │   ├── course/              ← Course detail screen
│   │   └── universities/        ← University screen
│   ├── app.json                 ← Expo app config (bundle IDs, plugins)
│   ├── eas.json                 ← EAS Build profiles (dev/preview/prod)
│   └── package.json
├── scraper/                     ← Data ingestion pipeline
│   ├── scrapers/                ← Per-university scrapers
│   │   ├── mit_ocw.py
│   │   ├── yale_ocw.py
│   │   ├── stanford.py
│   │   ├── harvard.py
│   │   ├── berkeley.py
│   │   ├── nptel.py
│   │   └── youtube_api.py       ← YouTube Data API client
│   ├── pipeline/
│   │   └── ingester.py          ← Normalises scraped data → DB upserts
│   ├── run_scrapers.py          ← CLI entry point: --source mit_ocw|all|…
│   └── requirements.txt
├── docker-compose.yml           ← Local dev: db + redis + backend + web + scraper
├── docker-compose.prod.yml      ← Production overrides (no port exposure, workers=2)
├── Makefile                     ← All common commands (see §4)
└── OPERATIONS.md                ← This file
```

The `opencourseware/` folder is used as a **git submodule** inside the workspace root (`Courses/`). The submodule is the authoritative git repo — all commits and pushes happen from inside `opencourseware/`.

---

## 2. Architecture Overview

```
Browser / Mobile
      │
      ▼
 Vercel CDN (ISR cache, 1 hr TTL)
      │
      ▼
 Next.js 14 (web)          Expo React Native (mobile)
      │                              │
      └──────────┬───────────────────┘
                 ▼
         FastAPI on Railway (or Render / Docker)
         /api/v1/…   ← rate-limited (200 req/min), gzip, Sentry
                 │
         ┌───────┴──────────┐
         ▼                  ▼
   PostgreSQL 16        Redis 7 (optional, 60-sec course-list cache)
```

**Key design decisions:**
- The homepage is a **server component** with ISR (`revalidate = 3600`). The full HTML is generated once and served from Vercel's edge CDN. No client-side waterfall on first load.
- The API is stateless; Redis is purely a read-through cache for the courses list endpoint. The app works without Redis — it degrades gracefully.
- JWT auth is only for the admin panel. Public endpoints are unauthenticated.
- Rate limit: 200 requests/minute per IP (enforced by `slowapi`).

---

## 3. Environment Variables

### Backend (`.env` in `backend/` or shell env)

| Variable | Required in Prod | Default (dev) | Description |
|----------|:---:|---|---|
| `DATABASE_URL` | ✅ | `postgresql+asyncpg://ocw:ocwpass@localhost:5432/opencourseware` | Full asyncpg connection string |
| `SECRET_KEY` | ✅ | `change-me-in-production` | JWT signing secret. Generate: `openssl rand -hex 32` |
| `ADMIN_EMAIL` | ✅ | `admin@example.com` | Admin user bootstrapped at startup |
| `ADMIN_PASSWORD` | ✅ | `changeme` | Admin password (bcrypt-hashed at startup) |
| `CORS_ORIGINS` | ✅ | `["http://localhost:3000"]` | JSON array **or** comma-separated list of allowed origins |
| `YOUTUBE_API_KEY` | ⚠️ optional | `""` | Required to enrich video metadata during scraping |
| `REDIS_URL` | ⚠️ optional | `redis://localhost:6379` | Omit or leave empty to disable caching |
| `SENTRY_DSN` | ⚠️ optional | `""` | Leave empty to disable error tracking |
| `ENVIRONMENT` | — | `development` | Set to `production` to enforce secret validation |
| `DEBUG` | — | `false` | Enables debug logging |

> **Important:** In `production` mode the app will **refuse to start** if `SECRET_KEY`, `ADMIN_PASSWORD`, `ADMIN_EMAIL`, or `CORS_ORIGINS` are left at their default values.

### Web (`web/.env.local` or Vercel dashboard)

| Variable | Required | Description |
|----------|:---:|---|
| `NEXT_PUBLIC_API_URL` | ✅ | Backend URL, e.g. `https://api.ocwexplorer.com` |
| `NEXT_PUBLIC_SENTRY_DSN` | ⚠️ optional | Sentry DSN for client-side error tracking |
| `SENTRY_AUTH_TOKEN` | ⚠️ optional | Sentry source map upload (set in Vercel env, not `.env.local`) |
| `SENTRY_ORG` | ⚠️ optional | Sentry org slug |
| `SENTRY_PROJECT` | ⚠️ optional | Sentry project slug |

### Mobile (set via EAS or inline in `eas.json`)

| Variable | Description |
|----------|---|
| `EXPO_PUBLIC_API_URL` | Backend URL for the native app |

EAS build profiles control which API URL is used:
- `development` → `http://localhost:8000`
- `preview` → `https://api-staging.ocwexplorer.com`
- `production` → `https://api.ocwexplorer.com`

### Docker Compose (`.env` at repo root, alongside `docker-compose.yml`)

```
POSTGRES_USER=ocw
POSTGRES_PASSWORD=<secret>
POSTGRES_DB=opencourseware
SECRET_KEY=<openssl rand -hex 32>
YOUTUBE_API_KEY=<your-key>
NEXT_PUBLIC_API_URL=http://localhost:8000
ADMIN_EMAIL=admin@example.com
ADMIN_PASSWORD=<secret>
CORS_ORIGINS=["http://localhost:3001","http://localhost:3000"]
```

---

## 4. Local Development

### Prerequisites

- Docker Desktop
- Node.js 20+
- Python 3.12+
- (Optional) YouTube Data API v3 key

### Option A — Docker Compose (recommended, all services at once)

```bash
cd opencourseware
cp .env.example .env          # fill in at minimum YOUTUBE_API_KEY
make up                       # builds images and starts all services
make migrate                  # run Alembic migrations
make scrape                   # populate the database
```

| Service | URL |
|---------|-----|
| Backend API + docs | http://localhost:8000 / http://localhost:8000/docs |
| Web app | http://localhost:3001 |
| PostgreSQL | localhost:5433 (mapped from container's 5432) |
| Redis | localhost:6379 |

Stop everything: `make down`

View logs: `make logs`

### Option B — Local (no Docker)

```bash
# 1. Backend
cd backend
python -m venv .venv
.venv\Scripts\activate        # Windows
pip install -r requirements.txt -r requirements-dev.txt
# Set DATABASE_URL in shell or .env
uvicorn app.main:app --reload --port 8000

# 2. Web
cd web
npm install
# Create web/.env.local: NEXT_PUBLIC_API_URL=http://localhost:8000
npm run dev                   # → http://localhost:3000

# 3. Mobile
cd mobile
npm install
npx expo start                # opens Expo dev tools
```

### Makefile Quick Reference

| Command | What it does |
|---------|---|
| `make up` | Build and start all Docker services |
| `make down` | Stop all services |
| `make build` | Rebuild Docker images without starting |
| `make logs` | Tail all service logs |
| `make migrate` | Run `alembic upgrade head` inside the backend container |
| `make scrape` | Run all scrapers |
| `make scrape-source SOURCE=mit_ocw` | Run a single scraper |
| `make test` | Run all tests (backend + scraper + web) |
| `make test-backend` | pytest in backend container |
| `make test-scraper` | pytest in scraper container |
| `make test-web` | Jest in web/ |
| `make shell-backend` | Open bash inside the running backend container |
| `make shell-db` | Open psql inside the running db container |
| `make dev-backend` | Run backend locally (no Docker) |
| `make dev-web` | Run web locally (no Docker) |
| `make install` | `pip install` + `npm install` for all subprojects locally |
| `make prod-up` | Start production Docker Compose stack |
| `make prod-migrate` | Run migrations in production stack |

---

## 5. Backend (FastAPI)

**Location:** `backend/`  
**Language:** Python 3.12  
**Framework:** FastAPI 0.111 + SQLAlchemy 2.0 async + Alembic  
**Database driver:** asyncpg (PostgreSQL 16)  
**Auth:** JWT via `python-jose` + `passlib[bcrypt]`

### API Routes

All routes are mounted at `/api/v1/`.

| Router | Prefix | Description |
|--------|--------|---|
| `courses.py` | `/courses` | List/filter/search courses, course detail, view count increment, featured endpoint |
| `universities.py` | `/universities` | List universities, university courses |
| `subjects.py` | `/subjects` | Subject taxonomy |
| `search.py` | `/search` | Full-text search across courses |
| `roadmaps.py` | `/roadmaps` | Learning roadmaps |
| `users.py` | `/users` | User profile (JWT-protected) |
| `admin.py` | `/admin` | Stats, scraper triggers, content management (JWT-protected) |

Interactive API docs: http://localhost:8000/docs (Swagger UI)

### Startup Behaviour

On startup (`lifespan` in `main.py`):
1. In production, validates all required env vars are non-default — **hard fails** if any are missing.
2. In development, auto-creates all tables via `Base.metadata.create_all`. **In production, use Alembic** (see §9).
3. Bootstraps the admin user (`ADMIN_EMAIL` / `ADMIN_PASSWORD`) if it doesn't already exist.

### Redis Caching

The courses list endpoint caches results in Redis for 60 seconds using the full filter parameters as the cache key. If Redis is unavailable, requests hit the database directly with no error surfaced.

### Rate Limiting

200 requests per minute per IP. Returns HTTP 429 if exceeded.

### Adding a New API Endpoint

1. Add a function to the appropriate `crud/` file.
2. Add request/response schemas to `schemas/`.
3. Add route handler to the appropriate `routers/` file.
4. Create an Alembic migration if you changed a model: `alembic revision --autogenerate -m "description"`.

---

## 6. Web Frontend (Next.js)

**Location:** `web/`  
**Framework:** Next.js 14 App Router  
**Language:** TypeScript  
**Styling:** Tailwind CSS  
**Data fetching:** TanStack Query v5 (client), `fetch` (server components)  
**State:** Zustand (UI state, saved courses)  
**Error tracking:** Sentry (`@sentry/nextjs`)  
**Testing:** Jest + Testing Library + MSW

### Pages

| Route | File | Type | Description |
|-------|------|------|---|
| `/` | `app/page.tsx` | Server (ISR) | Homepage: hero banner + course rows by subject |
| `/courses/[slug]` | `app/courses/` | Server + client | Course detail, video player |
| `/universities` | `app/universities/` | Client | University grid |
| `/universities/[slug]` | `app/universities/[slug]/` | Client | University course listing |
| `/subjects` | `app/subjects/` | Client | Subject browser |
| `/search` | `app/search/` | Client | Full-text search |
| `/browse` | `app/browse/` | Client | Filter courses |
| `/library` | `app/library/` | Client (Zustand) | Saved/bookmarked courses |
| `/roadmaps` | `app/roadmaps/` | Client | Learning roadmaps |
| `/admin` | `app/admin/` | Client (JWT) | Admin dashboard |

### ISR / Caching

- The homepage (`/`) has `export const revalidate = 3600` — it's generated server-side and cached at Vercel's CDN for 1 hour.
- The server component fetches the top 4 course rows (`featured`, `computer-science`, `machine-learning`, `mathematics`) on the first request; all others are loaded client-side via TanStack Query.
- Backend fetch timeout in ISR: 3 seconds. If the API is cold-starting, the page renders with partial data and the client fills in from cache.

### Mobile vs Desktop behaviour

The homepage uses Tailwind responsive classes to differ by viewport:

| Element | Mobile (< 768px) | Desktop (≥ 768px) |
|---------|-----------------|------------------|
| `HeroBanner` | Hidden | Visible |
| "Featured Courses" row | Hidden | Visible |
| `-mt-32` overlap | Off | On (content overlaps banner) |
| All other course rows | Visible | Visible |

**Tailwind breakpoints:** `sm` = 640px, `md` = 768px, `lg` = 1024px, `xl` = 1280px.

### PWA

The web app is a PWA. The service worker is registered via `app/layout.tsx`. The manifest is generated by `app/manifest.ts`. Cache headers for `sw.js` are set to `no-cache` in `next.config.js` to ensure updates are picked up immediately.

### Sentry

Configured in `sentry.client.config.ts`, `sentry.server.config.ts`, and `sentry.edge.config.ts`. Source maps are uploaded during build if `SENTRY_AUTH_TOKEN` is set.

### Bundle Analysis

```bash
cd web
npm run analyze    # builds and opens webpack bundle report
```

---

## 7. Mobile App (Expo)

**Location:** `mobile/`  
**Framework:** Expo SDK 51 + Expo Router 3.5  
**Language:** TypeScript  
**Navigation:** File-based (Expo Router), tab layout  
**Data fetching:** TanStack Query v5  
**Video:** `react-native-youtube-iframe`  
**Error tracking:** Sentry (`@sentry/react-native`)

### Screens

| Tab / Route | File | Description |
|-------------|------|---|
| Browse (Home) | `app/(tabs)/index.tsx` | Infinite-scroll grid of courses sorted by view count |
| Search | `app/(tabs)/search.tsx` | Full-text course search |
| Universities | `app/(tabs)/universities.tsx` | University grid → university courses |
| Saved | `app/(tabs)/saved.tsx` | Bookmarked courses (AsyncStorage) |
| Course detail | `app/course/[slug].tsx` | Course info + video player |

### Running locally

```bash
cd mobile
npm install
npx expo start              # Opens Expo dev server + QR code
```

- Press `a` to open Android emulator
- Press `i` to open iOS simulator
- Scan QR with Expo Go (physical device)

The dev build points `EXPO_PUBLIC_API_URL` to `http://localhost:8000`.

### EAS Builds (publishing native apps)

EAS (Expo Application Services) is used for native builds.

```bash
npm install -g eas-cli
eas login

# Development build (uses Expo Dev Client)
eas build --profile development --platform android

# Preview / internal testing
eas build --profile preview --platform all

# Production build (auto-increments version)
eas build --profile production --platform all

# Submit to app stores
eas submit --platform android    # uses google-service-account.json
eas submit --platform ios        # needs appleId, ascAppId, appleTeamId in eas.json
```

> **Note:** `eas.json` `submit.production.ios` fields (`appleId`, `ascAppId`, `appleTeamId`) must be filled in before submitting to App Store.

The `eas.json` EAS project ID (`extra.eas.projectId` in `app.json`) must also be filled in before EAS builds will work.

### App Config

| Setting | Value |
|---------|-------|
| App name | OCW Explorer |
| Expo slug | `ocw-explorer` |
| iOS bundle ID | `com.ocwexplorer.app` |
| Android package | `com.ocwexplorer.app` |
| URL scheme | `ocw://` |

---

## 8. Scraper Pipeline

**Location:** `scraper/`  
**Language:** Python 3.12  
**Libraries:** aiohttp, BeautifulSoup, YouTube Data API v3

### Data Sources

| Source key | Scraper file | Courses | Notes |
|------------|--------------|---------|-------|
| `mit_ocw` | `scrapers/mit_ocw.py` | ~2,563 | Reads from `MIT Course List Master.csv`; CSV must be present |
| `yale_ocw` | `scrapers/yale_ocw.py` | ~15 | Seed data + live enrichment |
| `stanford` | `scrapers/stanford.py` | ~13 | Seed data |
| `harvard` | `scrapers/harvard.py` | ~8 | Seed data |
| `berkeley` | `scrapers/berkeley.py` | ~10 | Seed data |
| `nptel` | `scrapers/nptel.py` | ~15 | Seed data |

### Running the Scraper

```bash
# All sources (Docker)
make scrape

# Single source (Docker)
make scrape-source SOURCE=mit_ocw

# All sources (native, from repo root)
cd scraper
DATABASE_URL=postgresql+asyncpg://ocw:ocwpass@localhost:5432/opencourseware \
YOUTUBE_API_KEY=<your-key> \
python run_scrapers.py --source all

# Single source (native)
python run_scrapers.py --source stanford
```

### Ingestion Pipeline

`pipeline/ingester.py` handles:
1. Upserts universities (by `slug`)
2. Upserts subjects (by `slug`)
3. Upserts courses (by `source_url`), linking to university + subjects
4. Upserts video records per course
5. Enriches video metadata via YouTube API if `YOUTUBE_API_KEY` is set

Courses are identified by `source_url` — re-running a scraper updates existing records rather than duplicating them.

### Adding a New Source

1. Create `scrapers/newuniversity.py` implementing the `BaseScraper` interface from `scrapers/base.py`.
2. Register the class in `scrapers/__init__.py`'s `SCRAPER_MAP`.
3. Run `make scrape-source SOURCE=newuniversity`.

---

## 9. Database & Migrations

**Engine:** PostgreSQL 16  
**ORM:** SQLAlchemy 2.0 (async)  
**Migrations:** Alembic

### Running Migrations

```bash
# In Docker
make migrate

# Production Docker Compose
make prod-migrate

# Native
cd backend
alembic upgrade head
```

### Creating a New Migration

```bash
cd backend
# After changing a model in app/models/:
alembic revision --autogenerate -m "describe your change"
# Review the generated file in migrations/versions/
alembic upgrade head
```

### Alembic Connection

The `alembic.ini` file has a **hardcoded fallback** URL (`postgresql://ocw:ocwpass@localhost:5432/opencourseware`). In practice, the `DATABASE_URL` env var overrides this. Always ensure the correct `DATABASE_URL` is set before running migrations in any environment.

### Schema Bootstrap (dev only)

In development mode (`ENVIRONMENT != production`), the backend auto-creates all tables on startup via `Base.metadata.create_all`. This is **disabled in production** — Alembic must be run explicitly.

### Direct DB Access

```bash
# Via Docker
make shell-db

# Native psql
psql postgresql://ocw:ocwpass@localhost:5432/opencourseware
```

---

## 10. Deployment

### How Deployment Works

**There are no GitHub Actions in this repo.** Deployment is triggered by:

- **Web (Vercel):** Vercel watches the `main` branch of `github.com/guzeman88/opencourseware-explorer` via native Git integration. Every push to `main` triggers a Vercel production deployment automatically. No secrets or workflow files needed.
- **Backend (Railway / Render):** Deployed via Docker. See below.

### Web → Vercel

| Property | Value |
|----------|-------|
| Vercel project | `opencourseware-explorer` |
| Vercel project ID | `prj_GSGPTvGL4NcbkOfEuALxfYciKoJD` |
| Vercel org ID | `team_XFGTZa1a7I91NQ5k3FK2J5up` |
| Git repo | `github.com/guzeman88/opencourseware-explorer` |
| Branch | `main` |
| Root directory | `web/` (configured in Vercel dashboard) |
| Build command | `npm run build` |
| Output | `.next/` |
| Deploys on | Every push to `main` |

**To deploy a web change:**
1. Make changes in `web/`
2. Commit and push to `main` from inside `opencourseware/`
3. Vercel detects the push and deploys automatically (~1–3 min)

**Environment variables** are set in the Vercel dashboard under the project settings. The critical one is `NEXT_PUBLIC_API_URL`.

### Backend → Railway

Railway is configured via `backend/railway.toml`. It builds using `backend/Dockerfile` and restarts on failure.

Railway reads env vars from the Railway dashboard (not from the repo). At minimum, set:
- `DATABASE_URL` (Railway can provision a Postgres database and inject this automatically)
- `SECRET_KEY`
- `ADMIN_EMAIL`
- `ADMIN_PASSWORD`
- `CORS_ORIGINS`

After deploying, run the initial migration from Railway's shell or trigger it as part of the deploy pipeline.

### Backend → Render (alternative)

`backend/render.yaml` defines a web service using Docker. Render reads env vars from the Render dashboard. `SECRET_KEY` is auto-generated by Render.

### Production Docker Compose (self-hosted)

Use when deploying to a VPS or VM.

```bash
# On the server
cd opencourseware
cp .env.example .env      # fill in all production values
make prod-up              # starts db + redis + backend + web (production config)
make prod-migrate         # run Alembic migrations
```

`docker-compose.prod.yml` differences from dev:
- No port exposure for db or redis (internal network only)
- No volume mounts for source code (uses built Docker image)
- 2 uvicorn workers with proxy header support
- Redis persistence enabled
- 512MB memory limits on all services
- Backend health check via `/health`

---

## 11. Making and Shipping Changes

### Git Workflow

The repo is `opencourseware/` (the git submodule). All git commands run from inside that directory.

```bash
cd opencourseware

# Check what's changed
git status

# Stage and commit
git add web/src/app/page.tsx
git commit -m "describe your change"

# Push → triggers Vercel deployment automatically
git push origin main
```

> PowerShell gotcha: paths with parentheses (like `mobile/app/(tabs)/index.tsx`) must be quoted:
> `git add "mobile/app/(tabs)/index.tsx"`

### Changing the Web UI

- **Homepage layout:** `web/src/app/page.tsx`
- **Responsive behaviour:** use Tailwind breakpoints. `md:` = 768px+. To hide on mobile: `hidden md:block`. To show only on mobile: `block md:hidden`.
- **Shared components:** `web/src/components/`
- **API calls (client-side):** `web/src/lib/` (axios-based API client) and hooks in `web/src/hooks/`
- **ISR revalidation:** `export const revalidate = 3600` in page files. Change the number (seconds) to adjust how often the CDN regenerates the page.

### Changing the Mobile App

- **Home/Browse screen:** `mobile/app/(tabs)/index.tsx`
- **Other tabs:** `mobile/app/(tabs)/`
- **Course detail:** `mobile/app/course/`
- Changes are visible immediately in Expo Go after saving (fast refresh).
- **To update the published native app:** you must run an EAS build and submit (see §7). A git push does not automatically update native app stores.

### Changing the API

1. Edit the router file in `backend/app/routers/`
2. Add/modify Pydantic schemas in `backend/app/schemas/`
3. If you changed DB models, create an Alembic migration (see §9)
4. Push to `main` — backend auto-redeploys on Railway/Render

### Adding a New Subject Row to the Homepage

In `web/src/app/page.tsx`, add a `<CourseRow>` component inside the main `<div>`:

```tsx
<CourseRow
  title="Your Subject Title"
  queryKey="unique-key"
  fetchType="subject"
  subjectSlug="your-subject-slug"
/>
```

The `subjectSlug` must match a slug in the database `subjects` table.

---

## 12. Testing

### Backend Tests

```bash
# Docker
make test-backend

# Native
cd backend
pytest -v
```

Tests use SQLite in-memory so no Postgres is required.

### Scraper Tests

```bash
# Docker
make test-scraper

# Native
cd scraper
pytest -v
```

### Web Tests

```bash
# Docker / native
make test-web

# Native
cd web
npm test
npm run test:coverage
```

Uses Jest + Testing Library + MSW for API mocking.

### Run All Tests

```bash
make test
```

---

## 13. Monitoring & Error Tracking

### Sentry

Both the backend and web frontend send errors to Sentry when `SENTRY_DSN` / `NEXT_PUBLIC_SENTRY_DSN` is configured. Traces sample rate is 20% on the backend.

To enable:
1. Create a project in sentry.io
2. Set `SENTRY_DSN` on Railway/Render (backend)
3. Set `NEXT_PUBLIC_SENTRY_DSN` in Vercel dashboard (web)
4. Set `SENTRY_AUTH_TOKEN`, `SENTRY_ORG`, `SENTRY_PROJECT` in Vercel for source map uploads

### Backend Health Check

```
GET /health
```

Returns `{"status": "ok"}`. Used by the production Docker Compose health check and Railway/Render uptime monitors.

### API Docs

```
GET /docs       ← Swagger UI
GET /redoc      ← ReDoc
GET /openapi.json
```

Available at the backend URL. Useful for testing endpoints manually.

---

## 14. Common Tasks

### Reseed the database from scratch

```bash
make shell-db
# Inside psql:
DROP SCHEMA public CASCADE;
CREATE SCHEMA public;
\q

make migrate
make scrape
```

### Run only the MIT scraper

```bash
make scrape-source SOURCE=mit_ocw
```

The MIT scraper reads from the CSV file at `MIT Course List Master - MIT Course List Master.csv` (repo root level, one directory up from `scraper/`). The path is resolved via `OCW_MIT_CSV` env var or defaults to the relative path.

### Update the admin password

Set `ADMIN_PASSWORD` env var to a new value and restart the backend. The password is bcrypt-hashed and stored at startup.

### Inspect the live database

On Railway: use the Railway dashboard's database shell, or connect directly with the connection string from the Railway dashboard.

On Docker: `make shell-db`

### Force-refresh Vercel ISR cache

Vercel does not expose a purge-by-URL API on the free/hobby plan. Options:
- Wait for the 1-hour TTL to expire
- Re-deploy (every deploy purges all ISR cache)
- Use `revalidatePath()` from a server action or API route (requires adding that logic)

### Check what's deployed

```bash
cd opencourseware
git log --oneline -10
```

The latest commit on `main` is what's deployed to Vercel and Railway.
