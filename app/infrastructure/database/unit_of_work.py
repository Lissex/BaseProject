from app.domain.interfaces.unit_of_work import UnitOfWork
from app.infrastructure.database.engine import async_session_maker
from app.infrastructure.repositories.refresh_token_repository import SQLAlchemyRefreshTokenRepository
from app.infrastructure.repositories.user_repository import SQLAlchemyUserRepository


class SQLAlchemyUnitOfWork(UnitOfWork):
    """
    Реализация UnitOfWork поверх SQLAlchemy AsyncSession.

    Использование в use-case:

        async with SQLAlchemyUnitOfWork() as uow:
            user = await uow.users.get_by_id(user_id)
            user.disable()
            await uow.users.update_user(user)
            await uow.commit()

    Если commit() не вызван (в т.ч. из-за исключения внутри блока),
    __aexit__ базового класса вызовет rollback() — незакоммиченные
    изменения не попадут в БД.
    """

    def __init__(self) -> None:
        self._session_maker = async_session_maker

    async def __aenter__(self) -> "SQLAlchemyUnitOfWork":
        self._session = self._session_maker()
        self.users = SQLAlchemyUserRepository(self._session)
        self.refresh_tokens = SQLAlchemyRefreshTokenRepository(self._session)
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        try:
            await super().__aexit__(exc_type, exc, tb)
        finally:
            await self._session.close()

    async def commit(self) -> None:
        await self._session.commit()

    async def rollback(self) -> None:
        await self._session.rollback()