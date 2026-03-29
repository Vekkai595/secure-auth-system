from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


class UserPublic(BaseModel):
    id: int
    email: EmailStr
    username: str
    is_active: bool
    is_verified: bool
    is_admin: bool
    created_at: datetime

    model_config = {'from_attributes': True}


class UserUpdate(BaseModel):
    username: str | None = Field(default=None, min_length=3, max_length=30)


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str = Field(min_length=12, max_length=128)
