from datetime import datetime, timedelta, timezone
from uuid import UUID

import jwt

from app.core.config.modules.jwt import JWTConfig
from app.core.exceptions.token import InvalidToken, TokenExpired
from app.domain.interfaces.token_service import TokenService

_TOKEN_TYPE = "access"


class JWTService(TokenService):
    def __init__(self, config: JWTConfig) -> None:
        self._secret = config.SECRET_KEY.get_secret_value()
        self._algorithm = config.ALGORITHM
        self._expire_minutes = config.ACCESS_TOKEN_EXPIRE_MINUTES

    def create_access_token(self, user_id: UUID) -> str:
        now = datetime.now(timezone.utc)
        payload = {
            "sub": str(user_id),
            "type": _TOKEN_TYPE,
            "iat": now,
            "exp": now + timedelta(minutes=self._expire_minutes),
        }
        return jwt.encode(payload, self._secret, algorithm=self._algorithm)

    def decode_access_token(self, token: str) -> UUID:
        try:
            payload = jwt.decode(token, self._secret, algorithms=[self._algorithm])
        except jwt.ExpiredSignatureError as exc:
            raise TokenExpired() from exc
        except jwt.InvalidTokenError as exc:
            raise InvalidToken() from exc

        if payload.get("type") != _TOKEN_TYPE:
            # Например кто-то попытался использовать refresh-токен как access,
            # или сюда попал токен другого типа/назначения.
            raise InvalidToken()

        try:
            return UUID(payload["sub"])
        except (KeyError, ValueError) as exc:
            raise InvalidToken() from exc