import random
import string

import factory

from app.domain.entities.user import User


def random_username() -> str:
    """
    Не используем factory.Faker("user_name") напрямую — Faker может
    генерировать точки/дефисы, которые не проходят regex Username
    (^[a-z0-9_]{3,20}$). Проще и надёжнее собрать вручную из
    разрешённого алфавита.
    """
    chars = string.ascii_lowercase + string.digits
    return "user_" + "".join(random.choices(chars, k=8))


def random_phone() -> str:
    """
    Валидный номер под правило PhoneNumber: 7 + [3489] + 9 цифр.
    Второй символ ограничен теми же цифрами, что и в VO
    (см. app/domain/value_objects/phone.py: r"^7[3489]\\d{9}$").
    """
    second_digit = random.choice("3489")
    rest = "".join(random.choices(string.digits, k=9))
    return f"+7{second_digit}{rest}"


class UserFactory(factory.Factory):
    """
    Фабрика для domain.User.

    User не создаётся через обычный __init__(**kwargs) с этими полями —
    у него собственный factory method .create(username, email, phone).
    Поэтому переопределяем _create, чтобы factory_boy звал именно его,
    а не пытался передать identity/security напрямую.

    Использование:
        user = UserFactory()                        # полностью случайный валидный User
        user = UserFactory(username="specific_name") # с конкретным полем, остальное случайное
    """

    class Meta:
        model = User

    username = factory.LazyFunction(random_username)
    email = factory.Faker("email")
    phone = factory.LazyFunction(random_phone)

    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        return model_class.create(*args, **kwargs)