from datetime import datetime, timedelta, timezone

from app.application.use_cases.logout import LogoutDTO, LogoutUseCase
from app.domain.entities.refresh_token import RefreshToken
from app.infrastructure.security.token_hasher import (generate_refresh_token,
                                                       hash_refresh_token)
from tests.factories import UserFactory
from tests.fakes import FakeUnitOfWork

EXPIRE_DAYS = 30


async def seed_token(uow: FakeUnitOfWork, user_id) -> str:
    plain = generate_refresh_token()
    token = RefreshToken.create(
        user_id=user_id,
        token_hash=hash_refresh_token(plain),
        expires_at=datetime.now(timezone.utc) + timedelta(days=EXPIRE_DAYS),
    )
    await uow.refresh_tokens.create(token)
    return plain


class TestLogoutSingleDevice:
    async def test_revokes_only_the_given_token(self):
        uow = FakeUnitOfWork()
        user = UserFactory()
        await uow.users.create_user(user)

        target_token = await seed_token(uow, user.id)
        other_token = await seed_token(uow, user.id)

        use_case = LogoutUseCase(uow=uow)
        await use_case.execute(LogoutDTO(refresh_token=target_token, all_devices=False))

        target_stored = await uow.refresh_tokens.get_by_hash(hash_refresh_token(target_token))
        other_stored = await uow.refresh_tokens.get_by_hash(hash_refresh_token(other_token))

        assert target_stored.is_revoked is True
        assert other_stored.is_revoked is False

    async def test_commits(self):
        uow = FakeUnitOfWork()
        user = UserFactory()
        await uow.users.create_user(user)
        token = await seed_token(uow, user.id)

        use_case = LogoutUseCase(uow=uow)
        await use_case.execute(LogoutDTO(refresh_token=token, all_devices=False))

        assert uow.committed is True


class TestLogoutAllDevices:
    async def test_revokes_all_tokens_of_the_user(self):
        uow = FakeUnitOfWork()
        user = UserFactory()
        await uow.users.create_user(user)

        token_a = await seed_token(uow, user.id)
        token_b = await seed_token(uow, user.id)

        use_case = LogoutUseCase(uow=uow)
        await use_case.execute(LogoutDTO(refresh_token=token_a, all_devices=True))

        stored_a = await uow.refresh_tokens.get_by_hash(hash_refresh_token(token_a))
        stored_b = await uow.refresh_tokens.get_by_hash(hash_refresh_token(token_b))

        assert stored_a.is_revoked is True
        assert stored_b.is_revoked is True

    async def test_does_not_affect_other_users_tokens(self):
        uow = FakeUnitOfWork()
        user_a = UserFactory()
        user_b = UserFactory()
        await uow.users.create_user(user_a)
        await uow.users.create_user(user_b)

        token_a = await seed_token(uow, user_a.id)
        token_b = await seed_token(uow, user_b.id)

        use_case = LogoutUseCase(uow=uow)
        await use_case.execute(LogoutDTO(refresh_token=token_a, all_devices=True))

        stored_b = await uow.refresh_tokens.get_by_hash(hash_refresh_token(token_b))
        assert stored_b.is_revoked is False


class TestLogoutIdempotency:
    async def test_unknown_token_does_not_raise(self):
        uow = FakeUnitOfWork()
        use_case = LogoutUseCase(uow=uow)

        # Не должно бросать исключение — logout с несуществующим/уже
        # неактуальным токеном достигает своей цели без действий.
        await use_case.execute(LogoutDTO(refresh_token="unknown-token", all_devices=False))

    async def test_unknown_token_does_not_commit(self):
        uow = FakeUnitOfWork()
        use_case = LogoutUseCase(uow=uow)

        await use_case.execute(LogoutDTO(refresh_token="unknown-token", all_devices=False))
        assert uow.committed is False

    async def test_already_revoked_token_does_not_raise(self):
        uow = FakeUnitOfWork()
        user = UserFactory()
        await uow.users.create_user(user)
        token = await seed_token(uow, user.id)

        use_case = LogoutUseCase(uow=uow)
        await use_case.execute(LogoutDTO(refresh_token=token, all_devices=False))
        # повторный logout тем же токеном — уже отозван, но не должен падать
        await use_case.execute(LogoutDTO(refresh_token=token, all_devices=False))