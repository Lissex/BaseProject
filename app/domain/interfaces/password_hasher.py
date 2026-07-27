from abc import ABC, abstractmethod


class PasswordHasher(ABC):
    """
    Контракт хэширования паролей.

    Domain (User.set_password) работает только с уже готовым хэшем и не
    знает, каким алгоритмом он получен — это ответственность infrastructure.
    Application-слой вызывает hash()/verify() перед тем как передать
    результат в User.
    """

    @abstractmethod
    def hash(self, plain_password: str) -> str:
        """Возвращает хэш пароля для сохранения в User/БД."""
        ...

    @abstractmethod
    def verify(self, plain_password: str, hashed_password: str) -> bool:
        """Сверяет введённый пароль с сохранённым хэшем."""
        ...