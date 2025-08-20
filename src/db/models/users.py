from src.db.base import Base
from sqlmodel import Column, Field
import sqlalchemy.dialects.postgresql as pg
from sqlmodel import Column, Field, String
from uuid import UUID, uuid4

class User(Base, table=True):
    __tablename__ = "users"

    id: UUID = Field(sa_column=Column(pg.UUID, primary_key=True, index=True, default=uuid4))
    username: str = Field(Column(String(50), unique=True, index=True, nullable=False))
    password: str = Field(Column(String(128), nullable=False))
