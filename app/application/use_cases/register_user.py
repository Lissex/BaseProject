from app.application.dto.register_user import RegisterUserDTO
from app.domain.entities.user import User
from app.domain.exceptions.users import (EmailAlreadyExists,
                                         InvalidPasswordFormat,
                                         PhoneAlreadyExists,
                                         UsernameAlreadyExists)
from app.domain.interfaces.password_hasher import PasswordHasher
from app.domain.interfaces.unit_of_work import UnitOfWork
from app.domain.value_objects.email import Email
from app.domain.value_objects.phone import PhoneNumber
from app.domain.value_objects.username import Username


class RegisterUserUseCase:
    """
    Регистрация нового пользователя.

    Шаги:
    1. Нормализовать/провалидировать username/email/phone через VO
       (иначе проверка уникальности по "сырым" данным может пропустить
       дубликат из-за разного регистра, например "John" vs "john").
    2. Проверить уникальность username/email/phone на уровне приложения
       (быстрый и понятный отказ до похода в БД на запись).
    3. Захэшировать пароль.
    4. Создать User, сохранить, закоммитить.

    Финальную защиту от гонки (два одновременных запроса с одинаковым
    username) обеспечивает repository.create_user — он транслирует
    IntegrityError от unique-констрейнтов БД в те же доменные исключения.
    """

    def __init__(self, uow: UnitOfWork, password_hasher: PasswordHasher) -> None:
        self._uow = uow
        self._password_hasher = password_hasher

    async def execute(self, dto: RegisterUserDTO) -> User:
        # Валидация формата + нормализация (lowercase для username и т.п.)
        # выполняется самими VO — если формат неверный, тут же вылетит
        # InvalidUsernameFormat / InvalidEmailFormat / InvalidPhoneFormat.
        username = Username(dto.username)
        email = Email(dto.email)
        phone = PhoneNumber(dto.phone)

        try:
            hashed_password = self._password_hasher.hash(dto.password)
        except ValueError as exc:
            # Например пароль длиннее 72 байт (ограничение bcrypt).
            raise InvalidPasswordFormat() from exc

        async with self._uow as uow:
            if await uow.users.get_by_username(username.value) is not None:
                raise UsernameAlreadyExists()

            if await uow.users.get_by_email(email.value) is not None:
                raise EmailAlreadyExists()

            if await uow.users.get_by_phone(phone.value) is not None:
                raise PhoneAlreadyExists()

            user = User.create(
                username=username.value,
                email=email.value,
                phone=phone.value,
            )
            user.set_password(hashed_password)

            await uow.users.create_user(user)
            await uow.commit()

            return user