from functools import lru_cache

from fastapi import Depends

from app.application.use_cases.login import LoginUseCase
from app.application.use_cases.logout import LogoutUseCase
from app.application.use_cases.refresh_token import RefreshTokenUseCase
from app.application.use_cases.register_user import RegisterUserUseCase
from app.core.config.settings import get_settings
from app.domain.interfaces.password_hasher import PasswordHasher
from app.domain.interfaces.token_service import TokenService
from app.domain.interfaces.unit_of_work import UnitOfWork
from app.infrastructure.database.unit_of_work import SQLAlchemyUnitOfWork
from app.infrastructure.security.jwt_service import JWTService
from app.infrastructure.security.password_hasher import BcryptPasswordHasher


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