.PHONY: up down build logs scrape scrape-source test test-backend test-scraper test-web migrate shell-backend shell-db install-backend install-web install-scraper prod-up prod-down prod-migrate prod-seed prod-backup

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

# ─── Production (Docker Compose) ──────────────────────────────────────────────
# Requires .env file with all production variables set.

prod-up:
	docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build

prod-down:
	docker compose -f docker-compose.yml -f docker-compose.prod.yml down

prod-migrate:
	docker compose -f docker-compose.yml -f docker-compose.prod.yml run --rm backend alembic upgrade head

prod-seed:
	@echo "Seeding MIT CSV..."
	docker compose -f docker-compose.yml -f docker-compose.prod.yml run --rm scraper python load_mit_csv.py
	@echo "Seeding comprehensive catalogue..."
	docker compose -f docker-compose.yml -f docker-compose.prod.yml run --rm scraper python scripts/load_courses.py
	@echo "Seeding done."

prod-backup:
	docker compose -f docker-compose.yml -f docker-compose.prod.yml exec db \
		pg_dump -U $${POSTGRES_USER:-ocw} $${POSTGRES_DB:-opencourseware} \
		| gzip > backups/backup_$$(date +%Y%m%dT%H%M%S).sql.gz
	@echo "Backup written to backups/"

# ─── Mobile ───────────────────────────────────────────────────────────────────

mobile-build-android:
	cd mobile && npx eas build --platform android --profile production

mobile-build-ios:
	cd mobile && npx eas build --platform ios --profile production

mobile-submit-android:
	cd mobile && npx eas submit --platform android --profile production

mobile-submit-ios:
	cd mobile && npx eas submit --platform ios --profile production
