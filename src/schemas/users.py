from __future__ import annotations
from typing import Optional
from uuid import UUID
from datetime import datetime

from pydantic import BaseModel, Field, constr

class UserBase(BaseModel):
    username: constr(min_length=4, max_length=50) = Field(..., description="Login username")

class UserCreate(UserBase):
    password: constr(min_length=8, max_length=128) = Field(..., description="Plain password (will be hashed before saving)")
    is_active: bool = Field(True, description="Whether the user is active")


class UserUpdate(BaseModel):
    username: Optional[constr(min_length=4, max_length=50)] = None
    password: Optional[constr(min_length=8, max_length=128)] = None
    is_active: Optional[bool] = None

class UserInDB(UserBase):
    id: UUID = Field(..., description="Primary UUID")
    hashed_password: str = Field(..., description="Hashed password stored in DB")
    is_active: bool = Field(True)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        orm_mode = True
        json_encoders = {
            UUID: lambda u: str(u),
            datetime: lambda d: d.isoformat(),
        }

class UserRead(UserBase):
    id: UUID = Field(..., description="Primary UUID")
    is_active: bool = Field(..., description="Is account active")
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        orm_mode = True
        json_encoders = {
            UUID: lambda u: str(u),
            datetime: lambda d: d.isoformat(),
        }

class UserLogin(BaseModel):
    username: constr(min_length=4, max_length=50) = Field(..., description="Login username")
    password: constr(min_length=8, max_length=128) = Field(..., description="Login password")

class Token(BaseModel):
    access_token: str = Field(..., description="JWT access token")
    token_type: str = Field("bearer", description="Token type (bearer)")

class TokenPayload(BaseModel):
    sub: Optional[str] = Field(None, description="Subject (user id)")
    exp: Optional[int] = Field(None, description="Expiration (unix timestamp)")
