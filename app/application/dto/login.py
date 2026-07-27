from dataclasses import dataclass


@dataclass(frozen=True)
class LoginDTO:
    """
    identifier — username или email, определяем по факту поиска,
    не заставляем клиента указывать тип явно.
    """
    identifier: str
    password: str


@dataclass(frozen=True)
class TokenPairDTO:
    access_token: str
    refresh_token: str
    token_type: str = "bearer"