"""
Fake-объекты (не Mock) для тестирования application-слоя без БД/крипто.

Почему Fake, а не unittest.mock.Mock/AsyncMock: use-case'ы делают
несколько последовательных вызовов к репозиторию (get_by_username,
затем create_user, и т.д.), и поведение одного вызова логически зависит
от другого (например, create_user должен быть виден в последующем
get_by_id). С голыми Mock пришлось бы вручную настраивать return_value
на каждый вызов и они не отражали бы реальную связность данных.
Fake — простая рабочая in-memory реализация того же интерфейса,
это даёт тестам вести себя ближе к реальности, оставаясь без БД.
"""

from uuid import UUID

from app.domain.entities.refresh_token import RefreshToken
from app.domain.entities.user import User
from app.domain.interfaces.password_hasher import PasswordHasher
from app.domain.interfaces.refresh_token import RefreshTokenRepository
from app.domain.interfaces.token_service import TokenService
from app.domain.interfaces.unit_of_work import UnitOfWork
from app.domain.interfaces.user_repository import UserRepository


class FakeUserRepository(UserRepository):
    def __init__(self) -> None:
        self._users: dict[UUID, User] = {}

    async def get_by_id(self, user_id: UUID) -> User | None:
        return self._users.get(user_id)

    async def get_by_username(self, username: str) -> User | None:
        return next((u for u in self._users.values() if u.username == username), None)

    async def get_by_email(self, email: str) -> User | None:
        return next((u for u in self._users.values() if u.email == email), None)

    async def get_by_phone(self, phone: str) -> User | None:
        return next((u for u in self._users.values() if u.phone == phone), None)

    async def create_user(self, user: User) -> None:
        self._users[user.id] = user

    async def update_user(self, user: User) -> None:
        self._users[user.id] = user


class FakeRefreshTokenRepository(RefreshTokenRepository):
    def __init__(self) -> None:
        self._tokens: dict[UUID, RefreshToken] = {}

    async def create(self, token: RefreshToken) -> None:
        self._tokens[token.id] = token

    async def get_by_hash(self, token_hash: str) -> RefreshToken | None:
        return next((t for t in self._tokens.values() if t.token_hash == token_hash), None)

    async def revoke(self, token: RefreshToken) -> None:
        self._tokens[token.id] = token

    async def revoke_all_for_user(self, user_id: UUID) -> None:
        for token in self._tokens.values():
            if token.user_id == user_id and not token.is_revoked:
                token.revoke()


class FakeUnitOfWork(UnitOfWork):
    """
    Не откатывает данные по-настоящему при rollback() (это не транзакция
    с БД, а просто словари в памяти, изменения в которые уже применены
    к моменту вызова commit/rollback) — только фиксирует факт, был ли
    commit. Этого достаточно для проверки бизнес-логики use-case'ов:
    тесты проверяют ЧТО должно было сохраниться и БЫЛ ли commit,
    а не поведение отката на уровне SQL.
    """

    def __init__(
        self,
        users: FakeUserRepository | None = None,
        refresh_tokens: FakeRefreshTokenRepository | None = None,
    ) -> None:
        self.users = users or FakeUserRepository()
        self.refresh_tokens = refresh_tokens or FakeRefreshTokenRepository()
        self.committed = False

    async def commit(self) -> None:
        self.committed = True

    async def rollback(self) -> None:
        # Мимикрируем поведение реальной БД: rollback() после успешного
        # commit() — no-op (транзакция уже закрыта). Без этой проверки
        # автоматический rollback в UnitOfWork.__aexit__ (который вызывается
        # ВСЕГДА при выходе из `async with`, см. базовый класс) затирал бы
        # committed=True обратно на False даже при успешном сценарии.
        if self.committed:
            return
        self.committed = False


class FakePasswordHasher(PasswordHasher):
    """
    Не настоящий bcrypt — просто предсказуемое обратимое отображение,
    чтобы тесты не платили за реальное CPU-тяжёлое хэширование и не
    зависели от деталей алгоритма. Сохраняет реальное поведение,
    важное для тестов: ValueError на слишком длинный пароль.
    """

    MAX_LENGTH = 72

    def hash(self, plain_password: str) -> str:
        if len(plain_password.encode("utf-8")) > self.MAX_LENGTH:
            raise ValueError("Password is too long")
        return f"hashed:{plain_password}"

    def verify(self, plain_password: str, hashed_password: str) -> bool:
        return hashed_password == f"hashed:{plain_password}"


class FakeTokenService(TokenService):
    def create_access_token(self, user_id: UUID) -> str:
        return f"access-token-for-{user_id}"

    def decode_access_token(self, token: str) -> UUID:
        prefix = "access-token-for-"
        if not token.startswith(prefix):
            raise ValueError("invalid fake token")
        return UUID(token.removeprefix(prefix))