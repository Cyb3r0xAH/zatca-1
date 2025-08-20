from src.db.base import Base
from sqlmodel import Field, Column, String
import sqlalchemy.dialects.postgresql as pg
from uuid import UUID, uuid4

class DBIsamAccount(Base, table=True):
    __tablename__ = 'dbisam_accounts'
    id: UUID = Field(sa_column=Column(pg.UUID, primary_key=True, default=uuid4))
    acc_no: str = Field(sa_column=Column(String(64), nullable=False))
    acc_name: str = Field(sa_column=Column(String(255), nullable=False))

class DBIsamItem(Base, table=True):
    __tablename__ = 'dbisam_items'
    id: UUID = Field(sa_column=Column(pg.UUID, primary_key=True, default=uuid4))
    item_no: str = Field(sa_column=Column(String(64), nullable=False))
    item_name: str = Field(sa_column=Column(String(255), nullable=False))

class DBIsamEntry(Base, table=True):
    __tablename__ = 'dbisam_entries'
    id: UUID = Field(sa_column=Column(pg.UUID, primary_key=True, default=uuid4))
    rec_id: int = Field(sa_column=Column(pg.INTEGER, nullable=False))
    acc_no: str = Field(sa_column=Column(String(64), nullable=False))
    amnt_db: float = Field(sa_column=Column(pg.FLOAT, nullable=False, default=0.0))
    item_no: str | None = Field(sa_column=Column(String(64), nullable=True))
    item_amnt: float | None = Field(sa_column=Column(pg.FLOAT, nullable=True))
    item_cont: float | None = Field(sa_column=Column(pg.FLOAT, nullable=True))

class DBIsamIndexEntry(Base, table=True):
    __tablename__ = 'dbisam_index_entries'
    id: UUID = Field(sa_column=Column(pg.UUID, primary_key=True, default=uuid4))
    rec_no: int = Field(sa_column=Column(pg.INTEGER, nullable=False))
    doc_no: int | None = Field(sa_column=Column(pg.INTEGER, nullable=True))
    doc_knd: int | None = Field(sa_column=Column(pg.INTEGER, nullable=True))
    acc_no: str | None = Field(sa_column=Column(String(64), nullable=True))
    mdate: str | None = Field(sa_column=Column(String(32), nullable=True))
    ratio: float | None = Field(sa_column=Column(pg.FLOAT, nullable=True))
    username: str | None = Field(sa_column=Column(String(255), nullable=True))
