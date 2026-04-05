from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from app.models.models import UserRole


# Схема для входа по телефону
class PhoneLoginRequest(BaseModel):
    phone: str = Field(..., pattern=r'^\+7\d{10}$')  # +7 и 10 цифр


class PhoneVerifyRequest(BaseModel):
    phone: str
    code: str


# Схемы для пользователей
class UserBase(BaseModel):
    phone: str
    name: str
    role: UserRole


class UserCreate(UserBase):
    password: Optional[str] = None


class UserResponse(UserBase):
    id: int
    is_active: int
    created_at: datetime

    class Config:
        from_attributes = True


# Схема для токена
class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


class PhoneLoginRequest(BaseModel):
    phone: str = Field(..., description="Номер телефона в формате +79991234567")

class PhoneVerifyRequest(BaseModel):
    phone: str
    code: str = Field(..., min_length=4, max_length=4)

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse