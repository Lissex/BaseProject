.PHONY: help install run \
        db-up db-down db-logs db-reset \
        migrate migrate-create migrate-down \
        lint format test

# Список команд. Без awk/grep — они по-разному ведут себя под cmd.exe (Windows)
# и bash (Linux/macOS/Git Bash), особенно с кавычками.
help:
	@echo Available commands:
	@echo   install         - install dependencies (uv sync)
	@echo   run             - run app locally with reload
	@echo   db-up           - start Postgres container
	@echo   db-down         - stop containers (keep data)
	@echo   db-reset        - stop and wipe db volume
	@echo   db-logs         - follow Postgres logs
	@echo   migrate         - apply all migrations (upgrade head)
	@echo   migrate-create  - create migration: make migrate-create m="description"
	@echo   migrate-down    - rollback last migration
	@echo   lint            - run ruff check
	@echo   format          - run ruff format
	@echo   test            - run pytest

# ==========================
# Установка / запуск
# ==========================

install: ## Установить зависимости (uv sync)
	uv sync

run: ## Запустить приложение локально (dev, с автоперезагрузкой)
	uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# ==========================
# Docker (Postgres)
# ==========================

db-up: ## Поднять Postgres в фоне
	docker compose up -d

db-down: ## Остановить контейнеры (данные сохраняются)
	docker compose down

db-reset: ## Остановить и удалить volume с данными БД (полный сброс)
	docker compose down -v

db-logs: ## Смотреть логи Postgres
	docker compose logs -f db

# ==========================
# Alembic
# ==========================

migrate: ## Применить все миграции (upgrade head)
	uv run alembic upgrade head

migrate-create: ## Создать новую миграцию: make migrate-create m="описание"
	uv run alembic revision --autogenerate -m "$(m)"

migrate-down: ## Откатить последнюю миграцию
	uv run alembic downgrade -1

# ==========================
# Качество кода
# ==========================

lint: ## Проверить код линтером (ruff)
	uv run ruff check .

format: ## Отформатировать код (ruff format)
	uv run ruff format .

test: ## Запустить тесты
	uv run pytest