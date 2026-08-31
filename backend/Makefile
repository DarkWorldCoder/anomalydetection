PYTHON ?= python3
VENV := .venv
BIN := $(VENV)/bin

.PHONY: setup db-up db-down migrate revision downgrade history current dev test docker-dev

setup:
	$(PYTHON) -m venv $(VENV)
	$(BIN)/pip install --upgrade pip
	$(BIN)/pip install -e ".[dev]"

db-up:
	docker compose up -d postgres

db-down:
	docker compose stop postgres

migrate:
	$(BIN)/alembic upgrade head

revision:
	@if [ -z "$(MSG)" ]; then echo 'Usage: make revision MSG="describe change"'; exit 1; fi
	$(BIN)/alembic revision --autogenerate -m "$(MSG)"

downgrade:
	$(BIN)/alembic downgrade -1

history:
	$(BIN)/alembic history --verbose

current:
	$(BIN)/alembic current

dev:
	$(BIN)/uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

test:
	$(BIN)/pytest

docker-dev:
	docker compose up --build
