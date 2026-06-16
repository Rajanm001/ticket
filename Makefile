PYTHON ?= python

.PHONY: setup run run-api test lint generate-data frontend-setup frontend

setup:
	$(PYTHON) -m pip install -r requirements.txt

generate-data:
	$(PYTHON) scripts/generate_data.py

# Single-command entry point: install deps, build the dataset, start the API.
run: setup generate-data run-api

run-api:
	uvicorn app.main:app --reload --port 8000

# Optional Next.js frontend (primary UI). Requires Node.js 18+.
frontend-setup:
	cd frontend && npm install

frontend:
	cd frontend && npm run dev

test:
	pytest -q

lint:
	$(PYTHON) -m compileall app tests scripts run.py
