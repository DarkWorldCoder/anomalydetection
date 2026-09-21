PYTHON ?= python3
VENV := .venv
BIN := $(VENV)/bin
PERFORMANCE_DATASET ?= datasets/dataset_4_sample_100_mixed.json
PERFORMANCE_RESULTS_DIR ?= performance/results
RECORDS ?= 100
WARMUP ?= 2
REPEATS ?= 10
HOST ?= http://127.0.0.1:8000
USERS ?= 10
SPAWN_RATE ?= 2
RUN_TIME ?= 60s
BATCH_SIZE ?= 10

.PHONY: setup db-up db-down migrate revision downgrade history current dev test benchmark load-test docker-dev

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

benchmark:
	$(BIN)/python scripts/benchmark_detection.py \
		--dataset $(PERFORMANCE_DATASET) \
		--records $(RECORDS) \
		--warmup $(WARMUP) \
		--repeats $(REPEATS) \
		--output $(PERFORMANCE_RESULTS_DIR)/model_benchmark.json

load-test:
	mkdir -p $(PERFORMANCE_RESULTS_DIR)
	REAL_DATASET_PATH=$(PERFORMANCE_DATASET) REAL_DATA_BATCH_SIZE=$(BATCH_SIZE) \
		$(BIN)/locust -f scripts/locustfile.py \
		--host $(HOST) \
		--headless \
		--users $(USERS) \
		--spawn-rate $(SPAWN_RATE) \
		--run-time $(RUN_TIME) \
		--json-file $(PERFORMANCE_RESULTS_DIR)/api_load.json \

docker-dev:
	docker compose up --build
