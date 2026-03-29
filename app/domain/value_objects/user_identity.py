from dataclasses import dataclass

from app.domain.value_objects.email import Email
from app.domain.value_objects.phone import PhoneNumber
from app.domain.value_objects.username import Username


@dataclass(frozen=True)
class UserIdentity:
    """Value Object для UserIdentity. Включает в себя username, email и phone. 
    Валидация при создании, инкапсуляция логики, например, проверки уникальности username или email."""
    
    username: Username
    email: Email
    phone: PhoneNumber