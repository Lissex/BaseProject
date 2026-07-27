from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class UserResponse(BaseModel):
    id: UUID
    username: str
    email: str
    phone: str
    is_active: bool
    is_email_verified: bool
    created_at: datetime