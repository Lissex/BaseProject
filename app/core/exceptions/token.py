class TokenException(Exception):
    """
    Базовый класс для технических исключений, связанных с токенами.

    Намеренно НЕ наследуется от DomainException — это не бизнес-ошибка
    домена (см. app/domain/exceptions/users.py docstring), а техническая
    проблема аутентификации. Форма (message/status_code) совпадает с
    DomainException специально — это позволяет использовать единый
    exception_handler в app/api/exception_handlers.py для обоих типов.
    """

    message: str = "Ошибка токена."
    status_code: int = 401

    def __init__(self, message: str | None = None, status_code: int | None = None):
        if message:
            self.message = message
        if status_code:
            self.status_code = status_code
        super().__init__(self.message)


class InvalidToken(TokenException):
    """Токен не прошёл проверку подписи/формата."""
    message = "Невалидный токен."


class TokenExpired(TokenException):
    """Токен просрочен."""
    message = "Токен истёк."


class TokenRevoked(TokenException):
    """Refresh-токен найден в БД, но отозван (logout/компрометация)."""
    message = "Токен отозван."