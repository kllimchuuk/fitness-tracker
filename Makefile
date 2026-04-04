
.PHONY: build up down logs makemigrations migrate run-ruff test test-setup

VENV = .venv
PYTEST = $(VENV)/bin/pytest

build:
	docker compose build

up:
	docker compose up -d

down:
	docker compose down

logs:
	docker compose logs -f

makemigrations:
	docker compose exec web python manage.py makemigrations

migrate:
	docker compose exec web python manage.py migrate

run-ruff:
	docker run --pull always -v .:/io --rm ghcr.io/astral-sh/ruff:latest format . \
	&& docker run --pull always -v .:/io --rm ghcr.io/astral-sh/ruff:latest check --fix .

test-setup:
	/usr/local/bin/python3.13 -m venv $(VENV)
	$(VENV)/bin/pip install -q -e ".[test]" whitenoise gunicorn daphne

test:
	DB_HOST=localhost $(PYTEST) tests/ --no-cov -q

test-cov:
	DB_HOST=localhost $(PYTEST) tests/ --cov-report=html && open htmlcov/index.html
