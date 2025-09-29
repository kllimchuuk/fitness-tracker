# Клонування репозиторія
Перед запуском проекту скопіюйте .env.example у .env і заповніть свої значення.
```bash

git clone https://github.com/kllimchuuk/fitness-tracker.git && cd fitness-tracker && cp .env.example .env && docker compose up --build
```
## Pre-commit

У проєкті використовується pre-commit для автоформатування, лінтингу та  фіксів перед комітом.

### Встановлення
```bash
pip install -r requirements-dev.txt
pre-commit install
```
