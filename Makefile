ifeq (,$(wildcard .env))
$(error .env file is missing. Please create one based on .env.example)
endif

include .env

CHECK_DIRS := .

mikasa-build:
	docker compose build

mikasa-run:
	docker compose up --build -d

mikasa-stop:
	docker compose stop

mikasa-delete:
	@if [ -d "long_term_memory" ]; then rm -rf long_term_memory; fi
	@if [ -d "short_term_memory" ]; then rm -rf short_term_memory; fi
	@if [ -d "generated_images" ]; then rm -rf generated_images; fi
	docker compose down

format-fix:
	uv run ruff format $(CHECK_DIRS) 
	uv run ruff check --select I --fix $(CHECK_DIRS)

lint-fix:
	uv run ruff check --fix $(CHECK_DIRS)

format-check:
	uv run ruff format --check $(CHECK_DIRS) 
	uv run ruff check -e $(CHECK_DIRS)
	uv run ruff check --select I -e $(CHECK_DIRS)

lint-check:
	uv run ruff check $(CHECK_DIRS)

.PHONY: help setup run-chainlit run-qdrant stop-qdrant

help:
	@echo "Available targets:"
	@echo "  setup         - Set up Python venv and install dependencies"
	@echo "  run-qdrant    - Start Qdrant vector DB via Docker"
	@echo "  stop-qdrant   - Stop Qdrant Docker container"
	@echo "  run-chainlit  - Run Chainlit app (native)"

setup:
	python3 -m venv .venv
	. .venv/bin/activate && pip install -U pip && pip install -e .

run-qdrant:
	docker run -d --rm --name qdrant-local -p 6334:6333 -v $(PWD)/long_term_memory:/qdrant/storage qdrant/qdrant:latest

stop-qdrant:
	docker stop qdrant-local || true

run-chainlit:
	. .venv/bin/activate && QDRANT_PORT=6334 chainlit run src/ai_companion/interfaces/chainlit/app.py --host 0.0.0.0 --port 8001