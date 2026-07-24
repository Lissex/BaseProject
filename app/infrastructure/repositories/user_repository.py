from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.user import User
from app.domain.interfaces.user_repository import UserRepository
from app.infrastructure.database.models.user import UserModel
from app.infrastructure.mappers.user_mapper import UserMapper


class SQLAlchemyUserRepository(UserRepository):
    """
    Реализация UserRepository поверх SQLAlchemy (async).

    Транзакцией управляет вызывающий код (UoW / зависимость сессии) —
    здесь только add/flush, без commit. Это соответствует контракту,
    описанному в UserRepository (см. app/domain/interfaces/user_repository.py).
    """

    def __init__(self, session: AsyncSession):
        self._session = session

    async def get_by_id(self, user_id: UUID) -> User | None:
        model = await self._session.get(UserModel, user_id)
        return UserMapper.to_domain(model) if model else None

    async def get_by_username(self, username: str) -> User | None:
        stmt = select(UserModel).where(UserModel.username == username)
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        return UserMapper.to_domain(model) if model else None

    async def get_by_email(self, email: str) -> User | None:
        stmt = select(UserModel).where(UserModel.email == email)
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        return UserMapper.to_domain(model) if model else None

    async def create_user(self, user: User) -> None:
        model = UserMapper.to_model(user)
        self._session.add(model)
        await self._session.flush()

    async def update_user(self, user: User) -> None:
        model = await self._session.get(UserModel, user.id)
        if model is None:
            # Не должно происходить при корректном использовании (get -> изменить -> update),
            # но лучше явная ошибка, чем тихий no-op.
            raise ValueError(f"UserModel с id={user.id} не найден для обновления")

        UserMapper.update_model(model, user)
        await self._session.flush()