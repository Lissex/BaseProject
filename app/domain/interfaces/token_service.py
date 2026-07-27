from abc import ABC, abstractmethod
from uuid import UUID


class TokenService(ABC):
    """
    Контракт для access-токенов.

    Только access — он stateless (JWT, не требует похода в БД на каждый
    запрос ради проверки). Refresh-токен НЕ JWT: это opaque-строка,
    хранимая в БД (см. RefreshTokenRepository) — ей всё равно нужен поход
    в БД для проверки отзыва, так что смысла в JWT-обёртке для неё нет,
    зато теряется удобство: JWT нельзя отозвать до истечения срока
    действия, не храня чёрный список — а раз БД всё равно нужна для
    отзыва, проще сделать refresh-токен изначально opaque и хранимым.
    """

    @abstractmethod
    def create_access_token(self, user_id: UUID) -> str: ...

    @abstractmethod
    def decode_access_token(self, token: str) -> UUID:
        """
        Возвращает user_id из валидного токена.
        Бросает InvalidToken / TokenExpired (app.core.exceptions.token)
        при проблемах с подписью/форматом/сроком действия.
        """
        ...