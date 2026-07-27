import pytest

from app.application.dto.login import LoginDTO
from app.application.use_cases.login import LoginUseCase
from app.domain.exceptions.users import InvalidCredentials, UserDisabled
from tests.factories import UserFactory
from tests.fakes import FakePasswordHasher, FakeTokenService, FakeUnitOfWork

PASSWORD = "secret123"
REFRESH_EXPIRE_DAYS = 30


async def seed_user(uow: FakeUnitOfWork, hasher: FakePasswordHasher, **overrides):
    user = UserFactory(**overrides)
    user.set_password(hasher.hash(PASSWORD))
    await uow.users.create_user(user)
    return user


def make_use_case(uow: FakeUnitOfWork, hasher: FakePasswordHasher) -> LoginUseCase:
    return LoginUseCase(
        uow=uow,
        password_hasher=hasher,
        token_service=FakeTokenService(),
        refresh_token_expire_days=REFRESH_EXPIRE_DAYS,
    )


class TestLoginSuccess:
    async def test_login_by_username_returns_token_pair(self):
        uow, hasher = FakeUnitOfWork(), FakePasswordHasher()
        user = await seed_user(uow, hasher, username="john_doe")
        use_case = make_use_case(uow, hasher)

        result = await use_case.execute(LoginDTO(identifier="john_doe", password=PASSWORD))

        assert result.access_token == f"access-token-for-{user.id}"
        assert result.refresh_token  # непустая строка
        assert uow.committed is True

    async def test_login_by_email_returns_token_pair(self):
        uow, hasher = FakeUnitOfWork(), FakePasswordHasher()
        user = await seed_user(uow, hasher, email="john@mail.com")
        use_case = make_use_case(uow, hasher)

        result = await use_case.execute(LoginDTO(identifier="john@mail.com", password=PASSWORD))

        assert result.access_token == f"access-token-for-{user.id}"

    async def test_identifier_is_case_insensitive(self):
        uow, hasher = FakeUnitOfWork(), FakePasswordHasher()
        await seed_user(uow, hasher, username="john_doe")
        use_case = make_use_case(uow, hasher)

        result = await use_case.execute(LoginDTO(identifier="JOHN_DOE", password=PASSWORD))
        assert result.access_token  # не упало

    async def test_persists_refresh_token(self):
        uow, hasher = FakeUnitOfWork(), FakePasswordHasher()
        await seed_user(uow, hasher, username="john_doe")
        use_case = make_use_case(uow, hasher)

        result = await use_case.execute(LoginDTO(identifier="john_doe", password=PASSWORD))

        from app.infrastructure.security.token_hasher import hash_refresh_token
        stored = await uow.refresh_tokens.get_by_hash(hash_refresh_token(result.refresh_token))
        assert stored is not None
        assert stored.is_valid is True


class TestLoginFailures:
    async def test_unknown_identifier_raises_invalid_credentials(self):
        uow, hasher = FakeUnitOfWork(), FakePasswordHasher()
        use_case = make_use_case(uow, hasher)

        with pytest.raises(InvalidCredentials):
            await use_case.execute(LoginDTO(identifier="ghost", password=PASSWORD))

        assert uow.committed is False

    async def test_wrong_password_raises_invalid_credentials(self):
        uow, hasher = FakeUnitOfWork(), FakePasswordHasher()
        await seed_user(uow, hasher, username="john_doe")
        use_case = make_use_case(uow, hasher)

        with pytest.raises(InvalidCredentials):
            await use_case.execute(LoginDTO(identifier="john_doe", password="wrong-password"))

    async def test_disabled_user_raises_user_disabled(self):
        uow, hasher = FakeUnitOfWork(), FakePasswordHasher()
        user = await seed_user(uow, hasher, username="john_doe")
        user.disable()
        await uow.users.update_user(user)
        use_case = make_use_case(uow, hasher)

        with pytest.raises(UserDisabled):
            await use_case.execute(LoginDTO(identifier="john_doe", password=PASSWORD))

    async def test_disabled_user_does_not_leak_before_password_check(self):
        """
        Неверный пароль для отключённого аккаунта всё равно должен дать
        InvalidCredentials, а не UserDisabled — иначе можно узнать, что
        аккаунт существует и отключён, не зная пароля.
        """
        uow, hasher = FakeUnitOfWork(), FakePasswordHasher()
        user = await seed_user(uow, hasher, username="john_doe")
        user.disable()
        await uow.users.update_user(user)
        use_case = make_use_case(uow, hasher)

        with pytest.raises(InvalidCredentials):
            await use_case.execute(LoginDTO(identifier="john_doe", password="wrong-password"))