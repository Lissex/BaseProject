import uuid
from dataclasses import replace
from datetime import datetime, timezone
from uuid import UUID

from app.domain.value_objects.email import Email
from app.domain.value_objects.phone import PhoneNumber
from app.domain.value_objects.user_identity import UserIdentity
from app.domain.value_objects.user_security import UserSecurity
from app.domain.value_objects.username import Username


class User:
    def __init__(
            self,
            id: UUID,
            identity: UserIdentity,
            security: UserSecurity,
            created_at: datetime,
            updated_at: datetime

            ):
        
        self._id = id
        self._identity = identity
        self._security = security
        self._created_at = created_at
        self._updated_at = updated_at


    """Properties - функции которые возвращают значения атрибутов класса"""

    @property
    def id(self) -> UUID:
        return self._id
    
    @property
    def username(self) -> str:
        return self._identity.username.value

    @property
    def email(self) -> str:
        return self._identity.email.value
    
    @property
    def phone(self) -> str:
        return self._identity.phone.value
    
    @property
    def hashed_password(self) -> str:
        return self._security.hashed_password
    
    @property
    def is_active(self) -> bool:
        return self._security.is_active

    @property
    def created_at(self) -> datetime:
        return self._created_at

    @property
    def updated_at(self) -> datetime:
        return self._updated_at

    @classmethod
    def create(cls, username: str, email: str, phone: str) -> "User":
        """Фабричный метод для создания нового пользователя. Генерирует UUID и устанавливает timestamps."""

        identity = UserIdentity(
            username=Username(username),
            email=Email(email),
            phone=PhoneNumber(phone)
        )
        security = UserSecurity(
            is_email_verified=False,
            is_active=True
        )

        return cls(
            id=uuid.uuid4(),
            identity=identity,
            security=security,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )

    def set_password(self, hashed_password: str):
            """Установить новый хеш пароля. Валидация на пустой пароль."""

            if not hashed_password:
                raise ValueError("Хеш пароля не может быть пустым")

            self._security = replace(self._security, hashed_password=hashed_password)
            self._updated_at = datetime.now(timezone.utc)

    def change_username(self, new_username: str):
        """Изменить username."""

        self._identity = UserIdentity(username=new_username, email=self.email)
        self._updated_at = datetime.now(timezone.utc)

    def change_email(self, new_email: str):
        """Изменить email и сбросить верификацию."""

        self._identity = UserIdentity(username=self.username, email=new_email)
        self._security = replace(self._security, is_email_verified=False)
        self._updated_at = datetime.now(timezone.utc)


    def change_phone(self, new_phone: str):
        """Изменить номер телефона."""

        self._identity = UserIdentity(username=self.username, email=self.email, phone=new_phone)
        self._updated_at = datetime.now(timezone.utc)

    



    def verify_email(self):
        """Метод для верификации email. Меняет статус в UserSecurity."""
        self._security = replace(self._security, is_email_verified=True)
        self._updated_at = datetime.now(timezone.utc)

    def disable(self):
        """Метод для деактивации пользователя. Меняет статус активности в UserSecurity."""
        self._security = replace(self._security, is_active=False)
        self._updated_at = datetime.now(timezone.utc)

    def enable(self):
        """Метод для активации пользователя. Меняет статус активности в UserSecurity."""
        self._security = replace(self._security, is_active=True)
        self._updated_at = datetime.now(timezone.utc)


    """Метод __repr__ возвращает строковое представление объекта класса User, которое включает его идентификатор (id). 
    Это полезно для отладки и логирования, так как позволяет легко увидеть, какой объект User был создан или используется."""
    def __repr__(self) -> str:
        return f"User(id={self._id})"
    
