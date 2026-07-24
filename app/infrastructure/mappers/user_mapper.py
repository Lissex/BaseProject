from app.domain.entities.user import User
from app.domain.value_objects.email import Email
from app.domain.value_objects.phone import PhoneNumber
from app.domain.value_objects.user_identity import UserIdentity
from app.domain.value_objects.user_security import UserSecurity
from app.domain.value_objects.username import Username
from app.infrastructure.database.models.user import UserModel


class UserMapper:
    """
    Преобразование между domain.User (rich model, VO) и UserModel (ORM, плоская).

    Данные из БД уже прошли валидацию при записи, поэтому повторная
    валидация VO при чтении (to_domain) — это просто защита от рассинхрона
    схемы/домена, а не лишняя работа "на всякий случай".
    """

    @staticmethod
    def to_domain(model: UserModel) -> User:
        identity = UserIdentity(
            username=Username(model.username),
            email=Email(model.email),
            phone=PhoneNumber(model.phone),
        )
        security = UserSecurity(
            hashed_password=model.hashed_password,
            is_active=model.is_active,
            is_email_verified=model.is_email_verified,
        )
        return User(
            id=model.id,
            identity=identity,
            security=security,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    @staticmethod
    def to_model(user: User) -> UserModel:
        """Для create_user — новая строка в БД."""
        return UserModel(
            id=user.id,
            username=user.username,
            email=user.email,
            phone=user.phone,
            hashed_password=user.hashed_password,
            is_active=user.is_active,
            is_email_verified=user._security.is_email_verified,
            created_at=user.created_at,
            updated_at=user.updated_at,
        )

    @staticmethod
    def update_model(model: UserModel, user: User) -> None:
        """
        Для update_user — обновляет уже загруженный ORM-объект in-place,
        вместо создания нового (иначе SQLAlchemy будет пытаться сделать INSERT
        или потребует merge).
        """
        model.username = user.username
        model.email = user.email
        model.phone = user.phone
        model.hashed_password = user.hashed_password
        model.is_active = user.is_active
        model.is_email_verified = user._security.is_email_verified
        model.updated_at = user.updated_at