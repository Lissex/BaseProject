import re
from dataclasses import dataclass

from app.domain.exceptions.users import InvalidPhoneFormat

"""Value Object для PhoneNumber. Валидация при создании, инкапсуляция логики, например, нормализация формата номера."""


@dataclass(frozen=True)
class PhoneNumber:
    value: str

    def __post_init__(self):
        normalized = self._normalize(self.value)
        object.__setattr__(self, "value", normalized)

    def _normalize(self, raw: str) -> str:
        digits = re.sub(r"[\s\-\(\)\+]", "", raw)
        if not digits.isdigit():
            raise InvalidPhoneFormat(raw)
        if len(digits) == 11 and digits[0] in ("7", "8"):
            digits = "7" + digits[1:]
        else:
            raise InvalidPhoneFormat(raw)
        if not re.match(r"^7[3489]\d{9}$", digits):
            raise InvalidPhoneFormat(raw)
        return f"+{digits}"

    def __str__(self) -> str:
        return self.value