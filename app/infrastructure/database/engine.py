from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import (AsyncSession, async_sessionmaker,
                                    create_async_engine)

from app.core.config.settings import settings

engine = create_async_engine(
    settings.db.url,
    echo=settings.db.ECHO,
    pool_pre_ping=True,
    # TODO: вынести pool_size/max_overflow в DatabaseConfig, если понадобится
    # настраивать их через env/yaml, а не только через is_prod.
    pool_size=10 if settings.is_prod else 5,
    max_overflow=20 if settings.is_prod else 10,
)

# expire_on_commit=False: объекты не становятся "истёкшими" после commit.
# Это правильно для async SQLAlchemy — сессия остаётся открытой,
# и мы можем продолжать работать с объектами без повторной загрузки из БД.
async_session_maker = async_sessionmaker(
    engine, expire_on_commit=False, class_=AsyncSession
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI-зависимость для инъекции сессии в роуты/репозитории.

    Использование:
        async def endpoint(db: AsyncSession = Depends(get_db)): ...

    Коммит НЕ делается здесь автоматически — управление транзакцией
    остаётся на уровне use-case / UoW, чтобы не закоммитить частично
    применённые изменения при ошибке в середине запроса.
    """
    async with async_session_maker() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise


async def dispose_engine() -> None:
    """
    Закрывает пул соединений. Вызывать на shutdown приложения
    (FastAPI lifespan), иначе при рестарте в контейнере могут
    оставаться зависшие соединения к БД.
    """
    await engine.dispose()