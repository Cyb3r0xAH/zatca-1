from __future__ import annotations
from typing import Optional
from uuid import UUID
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field, validator


class AccountBase(BaseModel):
    account_level: int = Field(..., description="Account hierarchy level")
    account_name: str = Field(..., description="Account name", max_length=150)
    account_debit: Decimal = Field(default=Decimal("0.00"))
    account_credit: Decimal = Field(default=Decimal("0.00"))
    account_ratio: Decimal = Field(default=Decimal("0.00"))

    @validator("account_debit", "account_credit", "account_ratio", pre=True)
    def _decimals(cls, v):
        return Decimal(str(v or "0"))


class AccountCreate(AccountBase):
    pass


class AccountUpdate(BaseModel):
    account_level: Optional[int] = None
    account_name: Optional[str] = None
    account_debit: Optional[Decimal] = None
    account_credit: Optional[Decimal] = None
    account_ratio: Optional[Decimal] = None

    @validator("account_debit", "account_credit", "account_ratio", pre=True)
    def _decimals(cls, v):
        if v is None:
            return v
        return Decimal(str(v))


class AccountRead(AccountBase):
    id: UUID = Field(..., description="Account UUID")
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        orm_mode = True
        json_encoders = {Decimal: lambda d: str(d), UUID: lambda u: str(u), datetime: lambda d: d.isoformat()}
