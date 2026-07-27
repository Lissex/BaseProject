import re
from dataclasses import dataclass

from app.domain.exceptions.users import InvalidEmailFormat

"""Value Object для Email. Валидация при создании, инкапсуляция логики, например, получения домена из email."""

EMAIL_REGEX = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"


@dataclass(frozen=True)
class Email:
    value: str  # Нужно объявить поле

    def __post_init__(self):
        normalized = self.value.strip().lower()

        if not re.match(EMAIL_REGEX, normalized):
            raise InvalidEmailFormat(self.value)

        object.__setattr__(self, "value", normalized)

    def __str__(self):
        return self.value

    @property
    def domain(self) -> str:
        """Пример инкапсуляции логики: VO может давать доп. данные"""
        return self.value.split('@')[-1]