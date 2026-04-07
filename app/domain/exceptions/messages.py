from dataclasses import dataclass


@dataclass(frozen=True)
class UserMessages:
    """Класс для хранения сообщений об ошибках, связанных с пользователем."""

    USERNAME_ALREADY_EXISTS: str = "Пользователь с таким именем уже существует."
    EMAIL_ALREADY_EXISTS: str = "Пользователь с таким email уже существует."
    PHONE_ALREADY_EXISTS: str = "Пользователь с таким номером телефона уже существует."
    INVALID_USERNAME: str = "Недопустимое имя пользователя."
    INVALID_EMAIL: str = "Недопустимый email."
    INVALID_PHONE: str = "Недопустимый номер телефона."
    NOT_FOUND: str = "Пользователь не найден."
    INACTIVE: str = "Пользователь неактивен."
    EMAIL_NOT_VERIFIED: str = "Email пользователя не подтвержден."
    INVALID_CURRENT_PASSWORD: str = "Неверный пароль."




user_messages = UserMessages()