from datetime import datetime, timedelta, timezone

from app.application.dto.login import LoginDTO, TokenPairDTO
from app.domain.entities.refresh_token import RefreshToken
from app.domain.exceptions.users import InvalidCredentials, UserDisabled
from app.domain.interfaces.password_hasher import PasswordHasher
from app.domain.interfaces.token_service import TokenService
from app.domain.interfaces.unit_of_work import UnitOfWork
from app.infrastructure.security.token_hasher import (generate_refresh_token,
                                                       hash_refresh_token)


class LoginUseCase:
    """
    Вход по username ИЛИ email + паролю.

    Умышленно не различаем в ответе "пользователь не найден" и
    "неверный пароль" — оба случая дают одинаковый InvalidCredentials.
    Раскрытие того, что конкретно не так, помогает перебору логинов
    (позволяет узнать, какие username/email вообще зарегистрированы).
    """

    def __init__(
        self,
        uow: UnitOfWork,
        password_hasher: PasswordHasher,
        token_service: TokenService,
        refresh_token_expire_days: int,
    ) -> None:
        self._uow = uow
        self._password_hasher = password_hasher
        self._token_service = token_service
        self._refresh_token_expire_days = refresh_token_expire_days

    async def execute(self, dto: LoginDTO) -> TokenPairDTO:
        identifier = dto.identifier.strip().lower()

        async with self._uow as uow:
            user = await uow.users.get_by_username(identifier)
            if user is None:
                user = await uow.users.get_by_email(identifier)

            if user is None:
                raise InvalidCredentials()

            if not self._password_hasher.verify(dto.password, user.hashed_password):
                raise InvalidCredentials()

            if not user.is_active:
                raise UserDisabled()

            access_token = self._token_service.create_access_token(user.id)

            plain_refresh_token = generate_refresh_token()
            refresh_token = RefreshToken.create(
                user_id=user.id,
                token_hash=hash_refresh_token(plain_refresh_token),
                expires_at=datetime.now(timezone.utc)
                + timedelta(days=self._refresh_token_expire_days),
            )
            await uow.refresh_tokens.create(refresh_token)
            await uow.commit()

            return TokenPairDTO(
                access_token=access_token,
                refresh_token=plain_refresh_token,
            )