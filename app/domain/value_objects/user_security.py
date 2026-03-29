from dataclasses import dataclass


@dataclass(frozen=True)
class UserSecurity:
    """Value Object для данных безопасности."""
    hashed_password: str = ""
    is_active: bool = True
    is_email_verified: bool = False