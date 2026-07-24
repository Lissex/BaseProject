import asyncio
from logging.config import fileConfig

from alembic import context
from sqlalchemy import pool
from sqlalchemy.ext.asyncio import create_async_engine

from app.core.config.settings import settings
from app.infrastructure.database.base import Base

# ВАЖНО: импорт моделей нужен, чтобы они зарегистрировались в Base.metadata —
# без этого Alembic не увидит таблицы при autogenerate. При добавлении новой
# модели (напр. app/infrastructure/database/models/order.py) добавляйте
# импорт сюда же.
from app.infrastructure.database.models.user import UserModel  # noqa: F401

# Alembic Config object — доступ к значениям из alembic.ini
config = context.config

# Логирование по конфигу из alembic.ini
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Метаданные для autogenerate — сравнение моделей с реальной схемой БД
target_metadata = Base.metadata


def get_url() -> str:
    """
    URL берём из settings (учитывает ENV: dev/prod/test), а не из alembic.ini —
    так конфигурация БД остаётся в одном месте и не рассинхронизируется
    между приложением и миграциями.
    """
    return settings.db.url.render_as_string(hide_password=False)


def run_migrations_offline() -> None:
    """
    Offline-режим: генерирует SQL без подключения к БД
    (alembic upgrade head --sql). Полезно для ревью миграций перед прод-деплоем.
    """
    context.configure(
        url=get_url(),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def _do_run_migrations(connection) -> None:
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()


async def run_migrations_online() -> None:
    """
    Online-режим: реальное подключение к БД через async-движок
    (тот же движок, что использует приложение — create_async_engine).
    """
    connectable = create_async_engine(get_url(), poolclass=pool.NullPool)

    async with connectable.connect() as connection:
        await connection.run_sync(_do_run_migrations)

    await connectable.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(run_migrations_online())