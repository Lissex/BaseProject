from datetime import datetime, timedelta, timezone

import pytest

from app.application.use_cases.refresh_token import RefreshTokenUseCase
from app.core.exceptions.token import InvalidToken, TokenExpired, TokenRevoked
from app.domain.entities.refresh_token import RefreshToken
from app.domain.exceptions.users import UserDisabled
from app.infrastructure.security.token_hasher import (generate_refresh_token,
                                                       hash_refresh_token)
from tests.factories import UserFactory
from tests.fakes import FakeTokenService, FakeUnitOfWork

REFRESH_EXPIRE_DAYS = 30


async def seed_user_with_token(
    uow: FakeUnitOfWork,
    *,
    is_active: bool = True,
    revoked: bool = False,
    expired: bool = False,
):
    user = UserFactory()
    if not is_active:
        user.disable()
    await uow.users.create_user(user)

    plain_token = generate_refresh_token()
    expires_at = (
        datetime.now(timezone.utc) - timedelta(days=1)
        if expired
        else datetime.now(timezone.utc) + timedelta(days=REFRESH_EXPIRE_DAYS)
    )
    token = RefreshToken.create(
        user_id=user.id,
        token_hash=hash_refresh_token(plain_token),
        expires_at=expires_at,
    )
    if revoked:
        token.revoke()
    await uow.refresh_tokens.create(token)

    return user, plain_token, token


def make_use_case(uow: FakeUnitOfWork) -> RefreshTokenUseCase:
    return RefreshTokenUseCase(
        uow=uow,
        token_service=FakeTokenService(),
        refresh_token_expire_days=REFRESH_EXPIRE_DAYS,
    )


class TestRefreshTokenSuccess:
    async def test_returns_new_token_pair(self):
        uow = FakeUnitOfWork()
        user, plain_token, _ = await seed_user_with_token(uow)
        use_case = make_use_case(uow)

        result = await use_case.execute(plain_token)

        assert result.access_token == f"access-token-for-{user.id}"
        assert result.refresh_token
        assert result.refresh_token != plain_token  # ротация — новый токен
        assert uow.committed is True

    async def test_revokes_old_token(self):
        uow = FakeUnitOfWork()
        _, plain_token, old_token = await seed_user_with_token(uow)
        use_case = make_use_case(uow)

        await use_case.execute(plain_token)

        stored_old = await uow.refresh_tokens.get_by_hash(old_token.token_hash)
        assert stored_old.is_revoked is True

    async def test_new_token_is_persisted_and_valid(self):
        uow = FakeUnitOfWork()
        _, plain_token, _ = await seed_user_with_token(uow)
        use_case = make_use_case(uow)

        result = await use_case.execute(plain_token)

        new_stored = await uow.refresh_tokens.get_by_hash(hash_refresh_token(result.refresh_token))
        assert new_stored is not None
        assert new_stored.is_valid is True


class TestRefreshTokenFailures:
    async def test_unknown_token_raises_invalid_token(self):
        uow = FakeUnitOfWork()
        use_case = make_use_case(uow)

        with pytest.raises(InvalidToken):
            await use_case.execute("some-random-token-that-does-not-exist")

    async def test_expired_token_raises_token_expired(self):
        uow = FakeUnitOfWork()
        _, plain_token, _ = await seed_user_with_token(uow, expired=True)
        use_case = make_use_case(uow)

        with pytest.raises(TokenExpired):
            await use_case.execute(plain_token)

    async def test_disabled_user_raises_user_disabled(self):
        uow = FakeUnitOfWork()
        _, plain_token, _ = await seed_user_with_token(uow, is_active=False)
        use_case = make_use_case(uow)

        with pytest.raises(UserDisabled):
            await use_case.execute(plain_token)


class TestRefreshTokenReuseDetection:
    async def test_reused_revoked_token_raises_token_revoked(self):
        uow = FakeUnitOfWork()
        _, plain_token, _ = await seed_user_with_token(uow, revoked=True)
        use_case = make_use_case(uow)

        with pytest.raises(TokenRevoked):
            await use_case.execute(plain_token)

    async def test_reuse_revokes_all_user_tokens(self):
        """
        Reuse detection: если предъявлен уже отозванный токен — это
        признак возможной компрометации, поэтому отзываются ВСЕ
        refresh-токены пользователя, а не только предъявленный.
        """
        uow = FakeUnitOfWork()
        user, plain_token, _ = await seed_user_with_token(uow, revoked=True)

        # Второй, ещё живой токен того же пользователя
        other_plain = generate_refresh_token()
        other_token = RefreshToken.create(
            user_id=user.id,
            token_hash=hash_refresh_token(other_plain),
            expires_at=datetime.now(timezone.utc) + timedelta(days=REFRESH_EXPIRE_DAYS),
        )
        await uow.refresh_tokens.create(other_token)

        use_case = make_use_case(uow)
        with pytest.raises(TokenRevoked):
            await use_case.execute(plain_token)

        stored_other = await uow.refresh_tokens.get_by_hash(other_token.token_hash)
        assert stored_other.is_revoked is True

    async def test_reuse_detection_commits_before_raising(self):
        """
        Массовый отзыв при reuse detection должен закоммититься, даже
        несмотря на то что use-case в итоге бросает исключение —
        иначе "защитная" реакция на компрометацию откатилась бы вместе
        с ошибкой (автоматический rollback в UnitOfWork.__aexit__).
        """
        uow = FakeUnitOfWork()
        _, plain_token, _ = await seed_user_with_token(uow, revoked=True)
        use_case = make_use_case(uow)

        with pytest.raises(TokenRevoked):
            await use_case.execute(plain_token)

        assert uow.committed is True