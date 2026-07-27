from functools import lru_cache
from uuid import UUID

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.application.use_cases.login import LoginUseCase
from app.application.use_cases.logout import LogoutUseCase
from app.application.use_cases.refresh_token import RefreshTokenUseCase
from app.application.use_cases.register_user import RegisterUserUseCase
from app.core.config.settings import get_settings
from app.core.exceptions.token import InvalidToken
from app.domain.entities.user import User
from app.domain.exceptions.users import UserDisabled
from app.domain.interfaces.password_hasher import PasswordHasher
from app.domain.interfaces.token_service import TokenService
from app.domain.interfaces.unit_of_work import UnitOfWork
from app.infrastructure.database.unit_of_work import SQLAlchemyUnitOfWork
from app.infrastructure.security.jwt_service import JWTService
from app.infrastructure.security.password_hasher import BcryptPasswordHasher

# auto_error=False + явная проверка ниже — чтобы при отсутствии заголовка
# получить наш InvalidToken (перехватывается общим exception_handler'ом,
# единый формат {"detail": ...}), а не дефолтный HTTPException от FastAPI
# со своим форматом ответа.
_bearer_scheme = HTTPBearer(auto_error=False)


def get_uow() -> UnitOfWork:
    """Новый UoW на каждый запрос — своя сессия/транзакция на запрос."""
    return SQLAlchemyUnitOfWork()


@lru_cache
def get_password_hasher() -> PasswordHasher:
    """Без состояния между запросами — можно кэшировать на процесс."""
    return BcryptPasswordHasher()


@lru_cache
def get_token_service() -> TokenService:
    return JWTService(get_settings().jwt)


def get_register_use_case(
    uow: UnitOfWork = Depends(get_uow),
    password_hasher: PasswordHasher = Depends(get_password_hasher),
) -> RegisterUserUseCase:
    return RegisterUserUseCase(uow=uow, password_hasher=password_hasher)


def get_login_use_case(
    uow: UnitOfWork = Depends(get_uow),
    password_hasher: PasswordHasher = Depends(get_password_hasher),
    token_service: TokenService = Depends(get_token_service),
) -> LoginUseCase:
    return LoginUseCase(
        uow=uow,
        password_hasher=password_hasher,
        token_service=token_service,
        refresh_token_expire_days=get_settings().jwt.REFRESH_TOKEN_EXPIRE_DAYS,
    )


def get_refresh_use_case(
    uow: UnitOfWork = Depends(get_uow),
    token_service: TokenService = Depends(get_token_service),
) -> RefreshTokenUseCase:
    return RefreshTokenUseCase(
        uow=uow,
        token_service=token_service,
        refresh_token_expire_days=get_settings().jwt.REFRESH_TOKEN_EXPIRE_DAYS,
    )


def get_logout_use_case(uow: UnitOfWork = Depends(get_uow)) -> LogoutUseCase:
    return LogoutUseCase(uow=uow)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer_scheme),
    token_service: TokenService = Depends(get_token_service),
    uow: UnitOfWork = Depends(get_uow),
) -> User:
    """
    Достаёт и валидирует access-токен из заголовка Authorization: Bearer,
    возвращает загруженного User.

    Порядок ошибок:
    - нет заголовка / не Bearer -> InvalidToken (401)
    - подпись/формат/срок токена невалидны -> InvalidToken/TokenExpired (401),
      бросает сам token_service.decode_access_token
    - токен валиден, но пользователя больше нет (удалён) -> InvalidToken (401):
      не раскрываем, что именно произошло, ведёт себя как "токен не годится"
    - пользователь найден, но деактивирован -> UserDisabled (403):
      здесь уже осознанно различаем от InvalidToken, т.к. это другая
      ситуация с точки зрения клиента (доступ заблокирован администратором,
      а не просто протухший токен)
    """
    if credentials is None:
        raise InvalidToken()

    user_id: UUID = token_service.decode_access_token(credentials.credentials)

    async with uow as uow:
        user = await uow.users.get_by_id(user_id)

    if user is None:
        raise InvalidToken()

    if not user.is_active:
        raise UserDisabled()

    return user