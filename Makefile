# ── CRM Database Makefile ─────────────────────────────────────────────────────
.PHONY: help up down logs migrate revision shell-db create-admin frontend-dev

help:
	@echo "Available commands:"
	@echo "  make up           - Start all Docker services"
	@echo "  make down         - Stop all services"
	@echo "  make logs         - Follow backend logs"
	@echo "  make migrate      - Run Alembic migrations"
	@echo "  make revision m=  - Create new migration (m='description')"
	@echo "  make shell-db     - psql shell into the database"
	@echo "  make create-admin - Create first superuser"
	@echo "  make frontend-dev - Start Vite dev server"
	@echo "  make dev          - Start DB + backend in dev mode"

# ── Docker ────────────────────────────────────────────────────────────────────
up:
	docker compose up -d --build

down:
	docker compose down

logs:
	docker compose logs -f backend

dev:
	docker compose up -d postgres
	uvicorn main:app --reload --host 0.0.0.0 --port 8000

# ── Database ──────────────────────────────────────────────────────────────────
migrate:
	alembic upgrade head

revision:
	alembic revision --autogenerate -m "$(m)"

shell-db:
	docker compose exec postgres psql -U $${POSTGRES_USER:-db_user} -d $${POSTGRES_DB:-crm_db}

# ── Admin ─────────────────────────────────────────────────────────────────────
create-admin:
	python scripts/create_admin.py

# ── Frontend ──────────────────────────────────────────────────────────────────
frontend-dev:
	cd frontend && npm run dev

frontend-build:
	cd frontend && npm run build
