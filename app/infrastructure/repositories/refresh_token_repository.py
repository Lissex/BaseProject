from uuid import UUID

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.refresh_token import RefreshToken
from app.domain.interfaces.refresh_token import RefreshTokenRepository
from app.infrastructure.database.models.refresh_token import RefreshTokenModel
from app.infrastructure.mappers.refresh_token_mapper import RefreshTokenMapper


class SQLAlchemyRefreshTokenRepository(RefreshTokenRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, token: RefreshToken) -> None:
        model = RefreshTokenMapper.to_model(token)
        self._session.add(model)
        await self._session.flush()

    async def get_by_hash(self, token_hash: str) -> RefreshToken | None:
        stmt = select(RefreshTokenModel).where(RefreshTokenModel.token_hash == token_hash)
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        return RefreshTokenMapper.to_domain(model) if model else None

    async def revoke(self, token: RefreshToken) -> None:
        model = await self._session.get(RefreshTokenModel, token.id)
        if model is None:
            raise ValueError(f"RefreshTokenModel с id={token.id} не найден для отзыва")
        model.revoked_at = token.revoked_at
        await self._session.flush()

    async def revoke_all_for_user(self, user_id: UUID) -> None:
        # Массовый UPDATE одним запросом — без загрузки каждой строки в Python,
        # т.к. logout "со всех устройств" может затронуть десятки записей.
        stmt = (
            update(RefreshTokenModel)
            .where(
                RefreshTokenModel.user_id == user_id,
                RefreshTokenModel.revoked_at.is_(None),
            )
            .values(revoked_at=func.now())
        )
        await self._session.execute(stmt)
        await self._session.flush()