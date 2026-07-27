import hashlib
import secrets


def generate_refresh_token() -> str:
    """Криптографически случайная opaque-строка — сам refresh-токен."""
    return secrets.token_urlsafe(64)


def hash_refresh_token(plain_token: str) -> str:
    """
    SHA-256, а НЕ bcrypt.

    bcrypt намеренно недетерминирован (разная соль на каждый вызов) —
    это плюс для паролей (защита от rainbow tables при переборе), но
    делает невозможным `SELECT ... WHERE token_hash = ?`: пришлось бы
    перебирать и bcrypt.checkpw() каждую строку в таблице.

    Refresh-токен — не пароль: это уже 512 бит случайности от
    generate_refresh_token(), не что-то, что можно перебрать по словарю.
    Детерминированный SHA-256 достаточен и позволяет искать по индексу.
    """
    return hashlib.sha256(plain_token.encode("utf-8")).hexdigest()