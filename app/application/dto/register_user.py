from dataclasses import dataclass


@dataclass(frozen=True)
class RegisterUserDTO:
    """
    Входные данные use-case регистрации.

    Намеренно НЕ pydantic-модель — application-слой не должен зависеть
    от FastAPI/pydantic напрямую. Валидация формата (regex и т.п.) уже
    входит в Value Objects на уровне domain; здесь просто перенос данных.
    """
    username: str
    email: str
    phone: str
    password: str