from app.domain.entities.refresh_token import RefreshToken
from app.infrastructure.database.models.refresh_token import RefreshTokenModel


class RefreshTokenMapper:
    @staticmethod
    def to_domain(model: RefreshTokenModel) -> RefreshToken:
        return RefreshToken(
            id=model.id,
            user_id=model.user_id,
            token_hash=model.token_hash,
            expires_at=model.expires_at,
            created_at=model.created_at,
            revoked_at=model.revoked_at,
        )

    @staticmethod
    def to_model(token: RefreshToken) -> RefreshTokenModel:
        return RefreshTokenModel(
            id=token.id,
            user_id=token.user_id,
            token_hash=token.token_hash,
            expires_at=token.expires_at,
            revoked_at=token.revoked_at,
            created_at=token.created_at,
        )