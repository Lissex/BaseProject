# syntax=docker/dockerfile:1

# =========================================================================
# Stage 1: builder — ставим зависимости в отдельном слое.
# Кэш Docker переиспользует этот слой, пока не поменяются
# pyproject.toml/uv.lock — пересборка кода не требует переустановки зависимостей.
# =========================================================================
FROM python:3.12-slim AS builder

# Официальный способ получить uv-бинарник без установки через pip
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy

# Сначала только манифесты — максимизирует переиспользование кэша слоя
COPY pyproject.toml uv.lock ./

RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-install-project --no-dev

# Теперь код — меняется чаще всего, поэтому копируется последним
COPY . .

RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev


# =========================================================================
# Stage 2: runtime — минимальный образ без uv/build-инструментов
# =========================================================================
FROM python:3.12-slim AS runtime

# Непривилегированный пользователь — не запускаем процесс от root
RUN groupadd --system app && useradd --system --gid app app

WORKDIR /app

COPY --from=builder --chown=app:app /app /app

ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

USER app

EXPOSE 8000

# Без --reload: это для разработки (make run), в контейнере не нужен
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]