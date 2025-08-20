from src.db.base import Base
from datetime import datetime
from sqlmodel import Field, Column, String
import sqlalchemy.dialects.postgresql as pg
from uuid import UUID, uuid4


class Group(Base, table=True):
    __tablename__ = "groups"
    
    id: UUID = Field(sa_column=Column(
        pg.UUID,
        primary_key=True,
        unique=True,
        default=uuid4
    ))
    group_name: str = Field(sa_column=Column(
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

    # items: list["InvoiceItemModel"] = Relationship(back_populates="group")
