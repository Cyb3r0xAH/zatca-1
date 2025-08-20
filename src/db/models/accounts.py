from src.db.base import Base
from datetime import datetime
from decimal import Decimal
import sqlalchemy.dialects.postgresql as pg
from sqlmodel import Column, Field, String
from uuid import UUID, uuid4

class Account(Base, table=True):
    __tablename__ = 'accounts'
    
    id: UUID = Field(sa_column=Column(
        pg.UUID,
        primary_key=True,
        unique=True,
        default=uuid4
    ))
    account_level: int = Field(sa_column=Column(
        pg.INTEGER,
        default=1,
        nullable=False,
    ))
    account_name: str = Field(sa_column=Column(
        String(150),
        nullable=False,
    ))
    account_debit: Decimal = Field(sa_column=Column(
        pg.NUMERIC(10, 2),
        nullable=False,
        default=0.0
    ))
    account_credit: Decimal = Field(sa_column=Column(
        pg.NUMERIC(10, 2),
        nullable=False,
        default=0.0
    ))
    account_ratio: Decimal = Field(sa_column=Column(
        pg.NUMERIC(10, 2),
        nullable=False,
        default=0.0
    ))
    created_at: datetime = Field(sa_column=Column(
        pg.TIMESTAMP(timezone=True),
        nullable=False,
        default=datetime.utcnow
    ))
    updated_at: datetime = Field(sa_column=Column(
        pg.TIMESTAMP(timezone=True),
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    ))