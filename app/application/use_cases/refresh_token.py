from datetime import datetime, timedelta, timezone

from app.application.dto.login import TokenPairDTO
from app.domain.entities.refresh_token import RefreshToken
from app.domain.exceptions.users import UserDisabled
from app.domain.interfaces.token_service import TokenService
from app.domain.interfaces.unit_of_work import UnitOfWork
from app.core.exceptions.token import InvalidToken, TokenExpired, TokenRevoked
from app.infrastructure.security.token_hasher import (generate_refresh_token,
                                                       hash_refresh_token)


class RefreshTokenUseCase:
    """
    Обновление access-токена по refresh-токену.

    Делает ротацию: старый refresh-токен отзывается, выдаётся новый.
    Это ограничивает время жизни украденного refresh-токена одним
    использованием — если его перехватят, легитимный клиент при
    следующем refresh получит ошибку (токен уже отозван) и это будет
    сигналом компрометации.

    Reuse detection: если ПОВТОРНО предъявлен уже отозванный токен —
    это явный признак того, что кто-то использует украденную копию
    (легитимный клиент уже получил новый и не стал бы слать старый
    снова). В этом случае отзываем ВСЕ refresh-токены пользователя —
    заставляем перелогиниться на всех устройствах.
    """

    def __init__(
        self,
        uow: UnitOfWork,
        token_service: TokenService,
        refresh_token_expire_days: int,
    ) -> None:
        self._uow = uow
        self._token_service = token_service
        self._refresh_token_expire_days = refresh_token_expire_days

    async def execute(self, plain_refresh_token: str) -> TokenPairDTO:
        token_hash = hash_refresh_token(plain_refresh_token)

        async with self._uow as uow:
            token = await uow.refresh_tokens.get_by_hash(token_hash)

            if token is None:
                raise InvalidToken()

            if token.is_revoked:
                # Reuse detection — см. docstring класса.
                await uow.refresh_tokens.revoke_all_for_user(token.user_id)
                await uow.commit()
                raise TokenRevoked()

            if token.is_expired:
                raise TokenExpired()

            user = await uow.users.get_by_id(token.user_id)
            if user is None or not user.is_active:
                raise UserDisabled()

            # Ротация: старый токен отзываем, выдаём новый.
            token.revoke()
            await uow.refresh_tokens.revoke(token)

            access_token = self._token_service.create_access_token(user.id)

            plain_new_refresh_token = generate_refresh_token()
            new_refresh_token = RefreshToken.create(
                user_id=user.id,
                token_hash=hash_refresh_token(plain_new_refresh_token),
                expires_at=datetime.now(timezone.utc)
                + timedelta(days=self._refresh_token_expire_days),
            )
            await uow.refresh_tokens.create(new_refresh_token)
            await uow.commit()

            return TokenPairDTO(
                access_token=access_token,
                refresh_token=plain_new_refresh_token,
            )