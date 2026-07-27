from abc import ABC, abstractmethod
from uuid import UUID

from app.domain.entities.user import User


class UserRepository(ABC):
    """
    Абстрактный интерфейс репозитория пользователей.

    Контракт:
    - get_* методы возвращают User | None
    - create_user и update_user возвращают None (транзакция управляется UoW)
    - create_user должен транслировать нарушение unique-констрейнтов БД
      (username/email/phone) в соответствующие DomainException
      (UsernameAlreadyExists/EmailAlreadyExists/PhoneAlreadyExists),
      а не пропускать "сырой" IntegrityError наружу — это подстраховка
      от гонки между проверкой уникальности в use-case и записью в БД.
    """

    @abstractmethod
    async def get_by_id(self, user_id: UUID) -> User | None: ...

    @abstractmethod
    async def get_by_username(self, username: str) -> User | None: ...

    @abstractmethod
    async def get_by_email(self, email: str) -> User | None: ...

    @abstractmethod
    async def get_by_phone(self, phone: str) -> User | None: ...

    @abstractmethod
    async def create_user(self, user: User) -> None: ...

    @abstractmethod
    async def update_user(self, user: User) -> None: ...