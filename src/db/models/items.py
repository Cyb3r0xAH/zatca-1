from src.db.base import Base
from datetime import datetime
from sqlmodel import Field, Column, String
import sqlalchemy.dialects.postgresql as pg
from sqlalchemy import ForeignKey
from uuid import UUID, uuid4

class Item(Base, table=True):
    __tablename__ = "items"

    id: UUID = Field(sa_column=Column(
        pg.UUID,
        primary_key=True,
        unique=True,
        default=uuid4
    ))
    item_name: str = Field(sa_column=Column(
        String(150),
        nullable=False,
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
    group_id: UUID = Field(sa_column=Column(
        pg.UUID, ForeignKey("groups.id", ondelete="CASCADE"), nullable=False
    ))