
.PHONY: build up down logs makemigrations migrate run-ruff

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
