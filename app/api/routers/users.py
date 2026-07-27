from fastapi import APIRouter, Depends

from app.api.dependencies import get_current_user
from app.api.schemas.user import UserResponse
from app.domain.entities.user import User

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)) -> UserResponse:
    return UserResponse(
        id=current_user.id,
        username=current_user.username,
        email=current_user.email,
        phone=current_user.phone,
        is_active=current_user.is_active,
        is_email_verified=current_user.is_email_verified,
        created_at=current_user.created_at,
    )