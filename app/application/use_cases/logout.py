from dataclasses import dataclass

from app.domain.interfaces.unit_of_work import UnitOfWork
from app.infrastructure.security.token_hasher import hash_refresh_token


@dataclass(frozen=True)
class LogoutDTO:
    refresh_token: str
    all_devices: bool = False


class LogoutUseCase:
    """
    Отзыв refresh-токена.

    Идемпотентен намеренно: если токен не найден или уже отозван/истёк —
    это не ошибка с точки зрения клиента. Цель logout — "этим токеном
    больше нельзя пользоваться", и если она уже достигнута (токена нет
    или он уже неактивен), выполнять logout повторно безопасно и не
    должно возвращать ошибку. Access-токен при этом продолжит работать
    до истечения своего короткого срока жизни — это ожидаемое поведение
    для stateless JWT без чёрного списка (см. app/domain/interfaces/token_service.py).
    """

    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    async def execute(self, dto: LogoutDTO) -> None:
        token_hash = hash_refresh_token(dto.refresh_token)

        async with self._uow as uow:
            token = await uow.refresh_tokens.get_by_hash(token_hash)
            if token is None:
                return

            if dto.all_devices:
                await uow.refresh_tokens.revoke_all_for_user(token.user_id)
            elif not token.is_revoked:
                token.revoke()
                await uow.refresh_tokens.revoke(token)

            await uow.commit()