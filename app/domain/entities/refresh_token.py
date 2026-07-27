import uuid
from datetime import datetime, timezone
from uuid import UUID


class RefreshToken:
    """
    Refresh-токен как агрегат.

    Хранит только ХЭШ токена (см. app/infrastructure/security/token_hasher.py) —
    сам plain-текст токена существует лишь в момент выдачи (возвращается
    клиенту) и никогда не сохраняется. Это то же соображение, что и с
    паролями: утечка БД не должна давать готовые токены для входа.
    """

    def __init__(
        self,
        id: UUID,
        user_id: UUID,
        token_hash: str,
        expires_at: datetime,
        created_at: datetime,
        revoked_at: datetime | None = None,
    ) -> None:
        self._id = id
        self._user_id = user_id
        self._token_hash = token_hash
        self._expires_at = expires_at
        self._created_at = created_at
        self._revoked_at = revoked_at

    @property
    def id(self) -> UUID:
        return self._id

    @property
    def user_id(self) -> UUID:
        return self._user_id

    @property
    def token_hash(self) -> str:
        return self._token_hash

    @property
    def expires_at(self) -> datetime:
        return self._expires_at

    @property
    def created_at(self) -> datetime:
        return self._created_at

    @property
    def revoked_at(self) -> datetime | None:
        return self._revoked_at

    @property
    def is_revoked(self) -> bool:
        return self._revoked_at is not None

    @property
    def is_expired(self) -> bool:
        return datetime.now(timezone.utc) >= self._expires_at

    @property
    def is_valid(self) -> bool:
        return not self.is_revoked and not self.is_expired

    @classmethod
    def create(cls, user_id: UUID, token_hash: str, expires_at: datetime) -> "RefreshToken":
        return cls(
            id=uuid.uuid4(),
            user_id=user_id,
            token_hash=token_hash,
            expires_at=expires_at,
            created_at=datetime.now(timezone.utc),
            revoked_at=None,
        )

    def revoke(self) -> None:
        if self._revoked_at is None:
            self._revoked_at = datetime.now(timezone.utc)

    def __repr__(self) -> str:
        return f"RefreshToken(id={self._id}, user_id={self._user_id}, valid={self.is_valid})"