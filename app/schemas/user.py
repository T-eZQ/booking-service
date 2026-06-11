from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr

from app.models.user import UserRole


class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str
    role: UserRole = UserRole.EMPLOYEE


class UserResponse(BaseModel):
    id: UUID
    username: str
    email: str
    role: UserRole
    created_at: datetime

    model_config = {"from_attributes": True}
