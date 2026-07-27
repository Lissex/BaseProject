import bcrypt

from app.domain.interfaces.password_hasher import PasswordHasher

# bcrypt имеет жёсткое ограничение в 72 байта на входной пароль — всё, что
# длиннее, молча обрезается самим алгоритмом. Это исторический источник
# багов (два разных длинных пароля с одинаковым префиксом считались бы
# одинаковыми), поэтому мы явно проверяем длину и кидаем ошибку вместо
# того чтобы позволить bcrypt обрезать пароль незаметно для пользователя.
_MAX_PASSWORD_BYTES = 72


class BcryptPasswordHasher(PasswordHasher):
    def __init__(self, rounds: int = 12) -> None:
        self._rounds = rounds

    def hash(self, plain_password: str) -> str:
        password_bytes = self._encode(plain_password)
        salt = bcrypt.gensalt(rounds=self._rounds)
        hashed = bcrypt.hashpw(password_bytes, salt)
        return hashed.decode("utf-8")

    def verify(self, plain_password: str, hashed_password: str) -> bool:
        password_bytes = self._encode(plain_password)
        try:
            return bcrypt.checkpw(password_bytes, hashed_password.encode("utf-8"))
        except ValueError:
            # Битый/несовместимый формат хэша в БД — не должно происходить
            # при нормальной работе, но лучше вернуть False, чем уронить
            # запрос авторизации с 500-й ошибкой.
            return False

    @staticmethod
    def _encode(plain_password: str) -> bytes:
        password_bytes = plain_password.encode("utf-8")
        if len(password_bytes) > _MAX_PASSWORD_BYTES:
            raise ValueError(
                f"Password is too long: {len(password_bytes)} bytes "
                f"(max {_MAX_PASSWORD_BYTES} bytes for bcrypt)"
            )
        return password_bytes