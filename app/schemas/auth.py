from pydantic import BaseModel, EmailStr, Field, field_validator


class RegisterRequest(BaseModel):
    email: EmailStr
    username: str = Field(min_length=3, max_length=30)
    password: str = Field(min_length=12, max_length=128)

    @field_validator('username')
    @classmethod
    def username_must_be_clean(cls, value: str) -> str:
        allowed = set('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-')
        if not set(value) <= allowed:
            raise ValueError('Username may contain only letters, digits, underscore, and hyphen')
        return value


class LoginRequest(BaseModel):
    identifier: str
    password: str


class RefreshRequest(BaseModel):
    refresh_token: str


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordConfirmRequest(BaseModel):
    reset_token: str
    new_password: str = Field(min_length=12, max_length=128)
