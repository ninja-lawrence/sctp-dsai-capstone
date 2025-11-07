SHELL := /bin/bash

.PHONY: dev test up down fmt lint

dev:
	python -m venv .venv && source .venv/bin/activate && pip install -r backend/requirements.txt || true
	# optional spaCy model
	python -m spacy download en_core_web_sm || true
	# run api and web
	( cd backend && uvicorn app.main:app --reload --port 8000 ) &
	( cd web && npm install && npm run dev )

test:
	( cd backend && pytest -q )
	( cd web && npx playwright install --with-deps && npm run test:e2e )

up:
	docker-compose up --build

down:
	docker-compose down


