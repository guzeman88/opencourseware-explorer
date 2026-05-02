.PHONY: up down build logs scrape scrape-source test test-backend test-scraper test-web migrate shell-backend shell-db

# ─── Docker Compose ────────────────────────────────────────────────────────────

up:
	docker compose up --build -d

down:
	docker compose down

build:
	docker compose build

logs:
	docker compose logs -f

# ─── Scrapers ──────────────────────────────────────────────────────────────────

scrape:
	docker compose run --rm scraper python run_scrapers.py --source all

scrape-source:
	docker compose run --rm scraper python run_scrapers.py --source $(SOURCE)

# ─── Tests ─────────────────────────────────────────────────────────────────────

test: test-backend test-scraper test-web

test-backend:
	docker compose run --rm backend pytest -v

test-scraper:
	docker compose run --rm scraper pytest -v

test-web:
	cd web && npm test -- --passWithNoTests

# ─── Database ──────────────────────────────────────────────────────────────────

migrate:
	docker compose run --rm backend alembic upgrade head

shell-db:
	docker compose exec db psql -U $${POSTGRES_USER:-ocw} -d $${POSTGRES_DB:-opencourseware}

# ─── Shell access ──────────────────────────────────────────────────────────────

shell-backend:
	docker compose exec backend bash

# ─── Local dev (no Docker) ────────────────────────────────────────────────────

install-backend:
	cd backend && pip install -r requirements.txt -r requirements-dev.txt

install-web:
	cd web && npm install

install-scraper:
	cd scraper && pip install -r requirements.txt

install: install-backend install-web install-scraper

dev-backend:
	cd backend && uvicorn app.main:app --reload --port 8000

dev-web:
	cd web && npm run dev
