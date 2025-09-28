
.PHONY: build up down logs migrations help

build:
	docker compose build

up:
	docker compose up -d

down:
	docker compose down

logs:
	docker compose logs -f

migrations:
	docker compose exec web python manage.py makemigrations
	docker compose exec web python manage.py migrate
