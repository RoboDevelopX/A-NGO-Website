# Common tasks. `make run` takes a fresh clone to a seeded, running site.
PYTHON ?= python3
VENV   := .venv
BIN    := $(VENV)/bin
PY     := $(BIN)/python
HOST   ?= 127.0.0.1
PORT   ?= 8000

.PHONY: help install setup run seed reseed train test lint format admin-password screenshots clean

help: ## Show available commands
	@grep -E '^[a-z-]+:.*## ' $(MAKEFILE_LIST) | awk -F':.*## ' '{printf "  %-16s %s\n", $$1, $$2}'

$(BIN)/activate:
	$(PYTHON) -m venv $(VENV)

$(VENV)/.installed: $(BIN)/activate requirements.txt requirements-dev.txt
	$(PY) -m pip install --upgrade pip
	$(PY) -m pip install -r requirements-dev.txt
	touch $@

install: $(VENV)/.installed ## Create the virtualenv and install dependencies

.env:
	$(PY) scripts/create_env.py

data/spam_model.joblib: $(VENV)/.installed
	$(PY) -m scripts.generate_spam_data
	$(PY) -m scripts.train_spam

setup: install .env data/spam_model.joblib seed ## Install, create .env, train the spam model, seed the DB

run: setup ## Start the seeded site on http://127.0.0.1:8000
	$(BIN)/uvicorn --factory app.main:create_app --reload --host $(HOST) --port $(PORT)

seed: install ## Seed demo content (idempotent: skips tables that already have rows)
	$(PY) -m app.seed

reseed: install ## Drop all demo data and seed again
	$(PY) -m app.seed --reset

train: install ## Regenerate the synthetic spam dataset and retrain the model
	$(PY) -m scripts.generate_spam_data
	$(PY) -m scripts.train_spam

test: install ## Run the test suite
	$(PY) -m pytest

lint: install ## Lint and check formatting
	$(BIN)/ruff check .
	$(BIN)/ruff format --check .

format: install ## Auto-format and fix lint issues
	$(BIN)/ruff format .
	$(BIN)/ruff check --fix .

admin-password: install ## Print a bcrypt hash for a new admin password
	$(PY) -m scripts.hash_password

screenshots: install ## Capture README screenshots and the social card (optional Playwright)
	$(PY) -m pip install -q -r requirements-tools.txt
	$(PY) -m scripts.screenshots

clean: ## Remove caches and generated data (keeps .env)
	rm -rf .pytest_cache .ruff_cache data/*.db data/*.db-* data/spam_dataset.csv data/spam_model.*
	find . -name __pycache__ -type d -prune -exec rm -rf {} +
