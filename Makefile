
.PHONY: build up down logs migrations help

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

lint:
	docker compose run --rm web ruff check .

format:
	docker compose run --rm web ruff formar .

format-check:
	docker compose run --rm web ruff format --check .
