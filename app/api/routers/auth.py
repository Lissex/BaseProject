from fastapi import APIRouter, Depends, status

from app.api.dependencies import (get_login_use_case, get_logout_use_case,
                                  get_refresh_use_case, get_register_use_case)
from app.api.schemas.auth import (LoginRequest, LogoutRequest,
                                  RefreshRequest, RegisterRequest,
                                  RegisterResponse, TokenResponse)
from app.application.dto.login import LoginDTO
from app.application.dto.register_user import RegisterUserDTO
from app.application.use_cases.login import LoginUseCase
from app.application.use_cases.logout import LogoutDTO, LogoutUseCase
from app.application.use_cases.refresh_token import RefreshTokenUseCase
from app.application.use_cases.register_user import RegisterUserUseCase

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=RegisterResponse, status_code=status.HTTP_201_CREATED)
async def register(
    payload: RegisterRequest,
    use_case: RegisterUserUseCase = Depends(get_register_use_case),
) -> RegisterResponse:
    dto = RegisterUserDTO(
        username=payload.username,
        email=payload.email,
        phone=payload.phone,
        password=payload.password,
    )
    user = await use_case.execute(dto)
    return RegisterResponse(id=user.id, username=user.username, email=user.email, phone=user.phone)


@router.post("/login", response_model=TokenResponse)
async def login(
    payload: LoginRequest,
    use_case: LoginUseCase = Depends(get_login_use_case),
) -> TokenResponse:
    dto = LoginDTO(identifier=payload.identifier, password=payload.password)
    result = await use_case.execute(dto)
    return TokenResponse(access_token=result.access_token, refresh_token=result.refresh_token)


@router.post("/refresh", response_model=TokenResponse)
async def refresh(
    payload: RefreshRequest,
    use_case: RefreshTokenUseCase = Depends(get_refresh_use_case),
) -> TokenResponse:
    result = await use_case.execute(payload.refresh_token)
    return TokenResponse(access_token=result.access_token, refresh_token=result.refresh_token)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    payload: LogoutRequest,
    use_case: LogoutUseCase = Depends(get_logout_use_case),
) -> None:
    dto = LogoutDTO(refresh_token=payload.refresh_token, all_devices=payload.all_devices)
    await use_case.execute(dto)