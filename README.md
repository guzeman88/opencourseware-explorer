# The Commons — OpenCourseWare Explorer

A Netflix-style platform for browsing 9,700+ free university courses from MIT, Yale, Stanford, Harvard, UC Berkeley, NPTEL, freeCodeCamp, and more — all on YouTube.

**Live site:** https://opencourseware-explorer.netlify.app  
**API:** https://opencourseware-api.onrender.com/docs  
**Repo:** https://github.com/guzeman88/opencourseware-explorer

> For setup instructions, deployment procedures, data protection, and team workflows see **[OPERATIONS.md](OPERATIONS.md)**.

---

## Architecture

```
opencourseware/
├── backend/          # FastAPI REST API (Python 3.12) → deployed on Render
├── scraper/          # Data ingestion pipeline (Python, run locally or on-demand)
├── web/              # Next.js 14 frontend (TypeScript, Tailwind) → deployed on Netlify
├── mobile/           # Expo React Native app (not yet deployed)
├── docker-compose.yml
└── Makefile
```

### Production Stack

| Layer | Technology | Host |
|-------|-----------|------|
| Frontend | Next.js 14.2 App Router, TypeScript, Tailwind CSS | Netlify |
| Backend API | FastAPI 0.111, SQLAlchemy 2.0 async | Render (free tier) |
| Database | PostgreSQL (Neon serverless) | Neon |
| Auth | JWT via `python-jose` + `pbkdf2_sha256` | — |
| Data fetching | TanStack Query v5 (client), `fetch` with ISR (server) | — |
| Error tracking | Sentry (`@sentry/nextjs`) | Sentry |
| Analytics | Google Analytics 4 (via `NEXT_PUBLIC_GA_MEASUREMENT_ID`) | Google |
| Scrapers | aiohttp, BeautifulSoup, YouTube Data API v3 | Local / manual |

---

## Quick Start (Local Development)

### Prerequisites
- Node.js 20+ and Python 3.12+
- A Neon account (or any PostgreSQL 15+ instance)
- YouTube Data API v3 key (for scraper enrichment)

### 1. Clone & configure

```bash
git clone https://github.com/guzeman88/opencourseware-explorer.git
cd opencourseware-explorer

cp .env.example .env
# Edit .env — see OPERATIONS.md §3 for every variable explained
```

### 2. Run the backend

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate          # Windows
pip install -r requirements.txt

# Point at your database
export DATABASE_URL="postgresql+asyncpg://..."
uvicorn app.main:app --reload --port 8000
# → http://localhost:8000/docs
```

### 3. Run the web frontend

```bash
cd web
npm install
# Optional: leave NEXT_PUBLIC_API_URL empty to use the built-in /api/v1 proxy.
# Set it only when you are intentionally running a local backend.
npm run dev
# → http://localhost:3000
```

---

## API Reference

Full interactive docs: https://opencourseware-api.onrender.com/docs

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/api/v1/courses` | — | List/filter courses with pagination |
| GET | `/api/v1/courses/featured` | — | Top view-count courses with video |
| GET | `/api/v1/courses/{slug}` | — | Course detail with video list |
| GET | `/api/v1/universities` | — | List universities |
| GET | `/api/v1/universities/{slug}/courses` | — | Courses by university |
| GET | `/api/v1/subjects` | — | Subject taxonomy |
| GET | `/api/v1/search?q=...` | — | Full-text course search |
| POST | `/api/v1/users/register` | — | Create user account |
| POST | `/api/v1/users/login` | — | Authenticate, returns JWT |
| GET | `/api/v1/users/me` | Bearer | Current user profile |
| GET | `/api/v1/users/me/library` | Bearer | Saved courses list |
| POST | `/api/v1/users/me/library` | Bearer | Bookmark a course |
| DELETE | `/api/v1/users/me/library/{id}` | Bearer | Remove bookmark |
| POST | `/api/v1/admin/auth/login` | — | Admin JWT login |
| GET | `/api/v1/admin/stats` | Admin | Platform statistics |

---

## Data Snapshot (as of May 2026)

| Source | Courses | Has Video |
|--------|---------|-----------|
| MIT OCW | ~2,573 | partial |
| NPTEL (IIT/IISc) | ~3,200 | most |
| Harvard | ~142 | most |
| freeCodeCamp | ~700 | all |
| CrashCourse | ~44 | all |
| Stanford | ~130 | most |
| UC Berkeley | ~300 | partial |
| Yale | ~42 | most |
| + 10 other sources | — | — |
| **Total** | **9,726** | **73.8% tagged** |

---

## Key Environment Variables

See `.env.example` and **[OPERATIONS.md §3](OPERATIONS.md)** for the complete reference.

| Variable | Where | Description |
|----------|-------|-------------|
| `DATABASE_URL` | Backend | Full asyncpg connection string to Neon |
| `SECRET_KEY` | Backend | JWT signing key — generate: `openssl rand -hex 32` |
| `YOUTUBE_API_KEY` | Scraper | Required for video enrichment |
| `API_UPSTREAM` | Frontend server/proxy | Backend URL used by SSR and `/api/v1` proxy |
| `NEXT_PUBLIC_API_URL` | Frontend browser | Leave empty to use relative `/api/v1`; set only for an intentional direct backend |
| `NEXT_PUBLIC_GA_MEASUREMENT_ID` | Frontend | Google Analytics 4 Measurement ID |

---

## License

All course content belongs to the respective universities and creators. This platform is an index/aggregator only.  
Application code: MIT License.

