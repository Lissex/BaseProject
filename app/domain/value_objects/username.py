import re
from dataclasses import dataclass

from app.domain.exceptions.users import InvalidUsernameFormat

"""Value Object для Username. Валидация при создании, инкапсуляция логики, например, нормализация формата имени пользователя."""

@dataclass(frozen=True)
class Username:
    value: str

    def __post_init__(self):
        # 1. Минимальная нормализация: убираем пробелы по бокам и в нижний регистр
        # Чтобы ' Admin' и 'admin' были одним и тем же объектом
        val = self.value.strip().lower()
        
        # 2. Одна проверка на всё: формат и длина (от 3 до 20 символов)
        if not re.match(r"^[a-z0-9_]{3,20}$", val):
            raise InvalidUsernameFormat(self.value)
        
        # Сохраняем уже чистый результат
        object.__setattr__(self, "value", val)

    def __str__(self) -> str:
        return self.value