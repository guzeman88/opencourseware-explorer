# OpenCourseWare Explorer

A Netflix-style platform for browsing thousands of free university courses from MIT, Yale, Stanford, Harvard, UC Berkeley, NPTEL and more — all on YouTube.

## Architecture

```
opencourseware/
├── backend/          # FastAPI REST API (Python 3.12)
├── scraper/          # Async scrapers + ingestion pipeline
├── web/              # Next.js 14 frontend (TypeScript, Tailwind)
├── mobile/           # Expo React Native app (planned)
├── docker-compose.yml
└── Makefile
```

### Stack

| Layer | Technology |
|-------|-----------|
| Backend API | FastAPI 0.111, SQLAlchemy 2.0 async, Alembic |
| Database | PostgreSQL 16 (asyncpg driver) |
| Cache/Queue | Redis 7 |
| Auth | JWT (python-jose + bcrypt) |
| Scrapers | aiohttp, BeautifulSoup, YouTube Data API v3 |
| Frontend | Next.js 14 App Router, TypeScript, Tailwind CSS |
| State | TanStack Query v5, Zustand |
| UI Primitives | Radix UI, Lucide Icons, Framer Motion |
| Video | react-player (YouTube embed) |
| Testing (BE) | pytest + pytest-asyncio, SQLite in-memory |
| Testing (FE) | Jest + Testing Library |
| Containers | Docker Compose |

## Quick Start

### Prerequisites
- Docker & Docker Compose
- Node.js 20+ (for local web dev)
- Python 3.12+ (for local backend/scraper dev)
- YouTube Data API v3 key (optional but recommended)

### 1. Clone & Configure

```bash
git clone <repo-url>
cd opencourseware

# Copy and fill in secrets
cp .env.example .env
# Edit .env: set POSTGRES_PASSWORD, SECRET_KEY, YOUTUBE_API_KEY, etc.
```

### 2. Start all services

```bash
make up
# or: docker compose up --build -d
```

Services:
- **Backend API**: http://localhost:8000  →  docs at http://localhost:8000/docs
- **Web App**: http://localhost:3000
- **PostgreSQL**: localhost:5432
- **Redis**: localhost:6379

### 3. Run scrapers to populate data

```bash
# Scrape all universities (requires YOUTUBE_API_KEY for video metadata)
make scrape

# Or scrape a single source
make scrape-source SOURCE=mit_ocw

# Available sources: mit_ocw, yale_ocw, stanford, nptel, berkeley, harvard, all
```

The MIT scraper reads from the provided CSV (2,563 courses). All other scrapers use curated seed data + live YouTube API enrichment.

## Development

### Backend

```bash
cd backend
python -m venv .venv && .venv/Scripts/activate  # Windows
pip install -r requirements.txt -r requirements-dev.txt

# Run with auto-reload
uvicorn app.main:app --reload --port 8000

# Run tests
pytest -v
```

### Web

```bash
cd web
npm install
cp .env.local.example .env.local  # set NEXT_PUBLIC_API_URL

npm run dev     # http://localhost:3000
npm test        # Jest tests
npm run build   # Production build
```

### Scrapers

```bash
cd scraper
pip install -r requirements.txt

# Run from project root with DATABASE_URL set
python run_scrapers.py --source mit_ocw
python run_scrapers.py --source all

# Tests
pytest -v
```

## API Reference

Full OpenAPI docs: http://localhost:8000/docs

### Key Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/v1/courses` | List/filter courses (pagination, search, filters) |
| GET | `/api/v1/courses/featured` | Top courses with video, sorted by views |
| GET | `/api/v1/courses/{slug}` | Course detail with videos |
| GET | `/api/v1/universities` | List universities |
| GET | `/api/v1/universities/{slug}/courses` | University's courses |
| GET | `/api/v1/subjects` | Subject taxonomy |
| GET | `/api/v1/search?q=...` | Full-text search |
| POST | `/api/v1/admin/auth/login` | Admin JWT login |
| GET | `/api/v1/admin/stats` | Platform statistics |
| POST | `/api/v1/admin/scraper/jobs` | Trigger scraper job |

### Course Filters

```
GET /api/v1/courses?q=algorithms&university_slug=mit&level=graduate&has_video_lectures=true&page=2&sort_by=view_count
```

Parameters: `q`, `university_slug`, `subject_slug`, `level`, `source_key`, `has_video_lectures`, `page`, `page_size`, `sort_by`, `sort_dir`

## Data Sources

| Source | Courses | Notes |
|--------|---------|-------|
| MIT OCW | 2,563 | From CSV; video lectures, notes, exams tracked |
| Stanford | 13 | CS229 ML, CS231n, CS224n NLP, CS285 RL, iOS, etc. |
| Yale | 15 | Death, Game Theory, Financial Markets, OYC series |
| Harvard | 8 | CS50 family, Justice, Abstract Algebra |
| UC Berkeley | 10 | CS61A/B/C, EE16A/B, CS285 |
| NPTEL | 15 | IIT/IISc courses across CS, Math, Physics, EE |

## Environment Variables

See `.env.example` for the full list. Key variables:

| Variable | Description |
|----------|-------------|
| `POSTGRES_*` | Database connection details |
| `SECRET_KEY` | JWT signing secret (generate with `openssl rand -hex 32`) |
| `YOUTUBE_API_KEY` | YouTube Data API v3 key for video metadata enrichment |
| `ADMIN_EMAIL` | Bootstrap admin user email |
| `ADMIN_PASSWORD` | Bootstrap admin user password |
| `NEXT_PUBLIC_API_URL` | Frontend → backend URL |

## Admin Panel

Navigate to http://localhost:3000/admin

Default credentials come from `.env` → `ADMIN_EMAIL` / `ADMIN_PASSWORD`.

Features:
- Dashboard with platform statistics
- Universities list
- Courses table with search/filter
- Scraper job triggers with live status polling

## Running Tests

```bash
# All backend tests
make test-backend

# All scraper tests
make test-scraper

# All web tests
make test-web

# Everything
make test
```

## Makefile Reference

```bash
make up              # Start all Docker services
make down            # Stop all services
make build           # Rebuild images
make scrape          # Run all scrapers
make scrape-source SOURCE=mit_ocw  # Single source
make test            # Run all tests
make test-backend    # Backend pytest
make test-scraper    # Scraper pytest
make test-web        # Web jest
make migrate         # Run Alembic migrations
make shell-backend   # Bash into backend container
make shell-db        # psql into database
make logs            # Follow all service logs
```

## License

All course content belongs to the respective universities. This platform is an aggregator/index only.
MIT License for the application code.
