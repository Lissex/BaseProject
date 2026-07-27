from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.user import User
from app.domain.exceptions.users import (EmailAlreadyExists,
                                         PhoneAlreadyExists,
                                         UsernameAlreadyExists)
from app.domain.interfaces.user_repository import UserRepository
from app.infrastructure.database.models.user import UserModel
from app.infrastructure.mappers.user_mapper import UserMapper


class SQLAlchemyUserRepository(UserRepository):
    """
    Реализация UserRepository поверх SQLAlchemy (async).

    Транзакцией управляет вызывающий код (UoW / зависимость сессии) —
    здесь только add/flush, без commit.
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

    async def get_by_phone(self, phone: str) -> User | None:
        stmt = select(UserModel).where(UserModel.phone == phone)
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        return UserMapper.to_domain(model) if model else None

    async def create_user(self, user: User) -> None:
        model = UserMapper.to_model(user)
        self._session.add(model)
        try:
            await self._session.flush()
        except IntegrityError as exc:
            # Подстраховка от гонки: use-case уже проверил уникальность
            # через get_by_username/get_by_email/get_by_phone, но между
            # проверкой и записью мог проскочить параллельный запрос.
            # Явный rollback не нужен — сессией дальше не пользуемся,
            # UnitOfWork.__aexit__ откатит её сам при выходе из блока.
            raise self._map_integrity_error(exc) from exc

    async def update_user(self, user: User) -> None:
        model = await self._session.get(UserModel, user.id)
        if model is None:
            raise ValueError(f"UserModel с id={user.id} не найден для обновления")

        UserMapper.update_model(model, user)
        await self._session.flush()

    @staticmethod
    def _map_integrity_error(exc: IntegrityError) -> Exception:
        """
        Определяет, какой unique-констрейнт нарушен, по тексту ошибки
        драйвера. Хрупко (зависит от имени колонки в сообщении asyncpg),
        но рабочий вариант, пока нет именованных constraint'ов с
        предсказуемыми названиями в модели.
        """
        detail = str(exc.orig).lower()
        if "username" in detail:
            return UsernameAlreadyExists()
        if "email" in detail:
            return EmailAlreadyExists()
        if "phone" in detail:
            return PhoneAlreadyExists()
        # Не удалось распознать — пробрасываем оригинал, чтобы не
        # проглотить незнакомую ошибку под неверным доменным исключением.
        return exc