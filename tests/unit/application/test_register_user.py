import pytest

from app.application.dto.register_user import RegisterUserDTO
from app.application.use_cases.register_user import RegisterUserUseCase
from app.domain.exceptions.users import (EmailAlreadyExists,
                                         InvalidPasswordFormat,
                                         PhoneAlreadyExists,
                                         UsernameAlreadyExists)
from tests.factories import UserFactory
from tests.fakes import FakePasswordHasher, FakeUnitOfWork


def make_use_case(uow: FakeUnitOfWork | None = None) -> tuple[RegisterUserUseCase, FakeUnitOfWork]:
    uow = uow or FakeUnitOfWork()
    use_case = RegisterUserUseCase(uow=uow, password_hasher=FakePasswordHasher())
    return use_case, uow


VALID_DTO = RegisterUserDTO(
    username="john_doe",
    email="john@mail.com",
    phone="+79991234567",
    password="secret123",
)


class TestRegisterUserSuccess:
    async def test_creates_and_persists_user(self):
        use_case, uow = make_use_case()

        user = await use_case.execute(VALID_DTO)

        assert user.username == "john_doe"
        assert user.email == "john@mail.com"
        assert user.phone == "+79991234567"
        assert await uow.users.get_by_id(user.id) is not None

    async def test_hashes_password_before_storing(self):
        use_case, _ = make_use_case()
        user = await use_case.execute(VALID_DTO)

        assert user.hashed_password == "hashed:secret123"
        assert user.hashed_password != "secret123"

    async def test_commits_transaction(self):
        use_case, uow = make_use_case()
        await use_case.execute(VALID_DTO)
        assert uow.committed is True

    async def test_normalizes_username_before_storing(self):
        use_case, _ = make_use_case()
        dto = RegisterUserDTO(
            username="John_Doe",  # смешанный регистр
            email=VALID_DTO.email,
            phone=VALID_DTO.phone,
            password=VALID_DTO.password,
        )
        user = await use_case.execute(dto)
        assert user.username == "john_doe"


class TestRegisterUserDuplicates:
    async def test_duplicate_username_raises_and_does_not_commit(self):
        uow = FakeUnitOfWork()
        existing = UserFactory(username="john_doe")
        await uow.users.create_user(existing)
        use_case, _ = make_use_case(uow)

        with pytest.raises(UsernameAlreadyExists):
            await use_case.execute(VALID_DTO)

        assert uow.committed is False

    async def test_duplicate_username_case_insensitive(self):
        """
        Регрессионный тест: проверка уникальности должна идти по
        нормализованному (lowercase) значению, иначе "John_Doe" и
        "john_doe" считались бы разными пользователями.
        """
        uow = FakeUnitOfWork()
        existing = UserFactory(username="john_doe")
        await uow.users.create_user(existing)
        use_case, _ = make_use_case(uow)

        dto = RegisterUserDTO(
            username="JOHN_DOE",
            email="another@mail.com",
            phone="+79997654321",
            password="secret123",
        )
        with pytest.raises(UsernameAlreadyExists):
            await use_case.execute(dto)

    async def test_duplicate_email_raises(self):
        uow = FakeUnitOfWork()
        existing = UserFactory(email="john@mail.com")
        await uow.users.create_user(existing)
        use_case, _ = make_use_case(uow)

        dto = RegisterUserDTO(
            username="another_user",
            email="john@mail.com",
            phone="+79997654321",
            password="secret123",
        )
        with pytest.raises(EmailAlreadyExists):
            await use_case.execute(dto)

    async def test_duplicate_phone_raises(self):
        uow = FakeUnitOfWork()
        existing = UserFactory(phone="+79991234567")
        await uow.users.create_user(existing)
        use_case, _ = make_use_case(uow)

        dto = RegisterUserDTO(
            username="another_user",
            email="another@mail.com",
            phone="+79991234567",
            password="secret123",
        )
        with pytest.raises(PhoneAlreadyExists):
            await use_case.execute(dto)


class TestRegisterUserPassword:
    async def test_too_long_password_raises_invalid_password_format(self):
        use_case, _ = make_use_case()
        dto = RegisterUserDTO(
            username=VALID_DTO.username,
            email=VALID_DTO.email,
            phone=VALID_DTO.phone,
            password="x" * 73,  # больше лимита FakePasswordHasher/bcrypt (72 байта)
        )

        with pytest.raises(InvalidPasswordFormat):
            await use_case.execute(dto)