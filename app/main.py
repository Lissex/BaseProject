from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.exception_handlers import register_exception_handlers
from app.api.routers.auth import router as auth_router
from app.core.config.settings import settings
from app.infrastructure.database.engine import dispose_engine


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    # --- startup ---
    # Сюда позже можно добавить прогрев кэша, проверку доступности БД
    # (SELECT 1) перед приёмом трафика и т.п.
    yield
    # --- shutdown ---
    # Обязательно закрываем пул соединений — иначе при рестарте
    # в контейнере могут оставаться зависшие коннекты к Postgres.
    await dispose_engine()


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.app.TITLE,
        debug=settings.app.DEBUG,
        lifespan=lifespan,
    )

    register_exception_handlers(app)

    app.include_router(auth_router)

    return app


app = create_app()