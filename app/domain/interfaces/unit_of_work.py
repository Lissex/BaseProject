from abc import ABC, abstractmethod
from types import TracebackType

from app.domain.interfaces.refresh_token import RefreshTokenRepository
from app.domain.interfaces.user_repository import UserRepository


class UnitOfWork(ABC):
    """
    Абстрактный контракт Unit of Work.

    Инкапсулирует границу транзакции: use-case открывает UoW через
    `async with`, работает с репозиториями внутри, и либо явно вызывает
    commit(), либо — если этого не произошло — при выходе из блока
    (в т.ч. из-за исключения) транзакция откатывается автоматически.

    Repository-атрибуты (users, refresh_tokens и т.д.) должны быть
    доступны только внутри блока `async with` — до входа или после
    выхода обращение к ним не гарантировано и не должно использоваться.
    """

    users: UserRepository
    refresh_tokens: RefreshTokenRepository

    async def __aenter__(self) -> "UnitOfWork":
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        # Если commit() не был вызван явно внутри блока — откатываем.
        # Это же сработает при исключении: commit не успел выполниться.
        await self.rollback()

    @abstractmethod
    async def commit(self) -> None: ...

    @abstractmethod
    async def rollback(self) -> None: ...