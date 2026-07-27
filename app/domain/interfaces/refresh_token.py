from abc import ABC, abstractmethod
from uuid import UUID

from app.domain.entities.refresh_token import RefreshToken


class RefreshTokenRepository(ABC):
    """
    Контракт хранения refresh-токенов.

    create/revoke/revoke_all_for_user не коммитят — как и в UserRepository,
    транзакция управляется UnitOfWork.
    """

    @abstractmethod
    async def create(self, token: RefreshToken) -> None: ...

    @abstractmethod
    async def get_by_hash(self, token_hash: str) -> RefreshToken | None: ...

    @abstractmethod
    async def revoke(self, token: RefreshToken) -> None:
        """Сохраняет состояние уже отозванного (token.revoke() вызван) токена."""
        ...

    @abstractmethod
    async def revoke_all_for_user(self, user_id: UUID) -> None:
        """Logout со всех устройств — массовый отзыв."""
        ...