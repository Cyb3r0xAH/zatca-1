from src.db.base import Base
from datetime import datetime
from decimal import Decimal
from sqlmodel import Field, Relationship, Column, String
import sqlalchemy.dialects.postgresql as pg
from sqlalchemy import ForeignKey
from uuid import UUID, uuid4
from enum import Enum

class InvoiceStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    DONE = "done"
    FAILED = "failed"

class Invoice(Base, table=True):
    __tablename__ = "invoices"

    id: UUID = Field(sa_column=Column(pg.UUID, primary_key=True, unique=True, default=uuid4))
    invoice_number: str = Field(sa_column=Column(String(255), nullable=False, unique=True))
    store_name: str = Field(sa_column=Column(String(255), nullable=False))
    store_address: str = Field(sa_column=Column(String(255), nullable=False))
    vat_number: str = Field(sa_column=Column(String(255), nullable=False))
    date: datetime = Field(sa_column=Column(pg.TIMESTAMP(timezone=True), nullable=False))
    total: Decimal = Field(sa_column=Column(pg.NUMERIC(10, 2), default=Decimal("0.00"), nullable=False))
    taxes: Decimal = Field(sa_column=Column(pg.NUMERIC(10, 2), default=Decimal("0.00"), nullable=False))
    seller_taxes: Decimal = Field(sa_column=Column(pg.NUMERIC(10, 2), default=Decimal("0.00"), nullable=False))
    net_total: Decimal = Field(sa_column=Column(pg.NUMERIC(10, 2), default=Decimal("0.00"), nullable=False))
    user_name: str = Field(sa_column=Column(String(255), nullable=False))
    account_id: str = Field(sa_column=Column(String(255), nullable=False))
    status: InvoiceStatus = Field(
        sa_column=Column(
            pg.ENUM(InvoiceStatus, name="invoice_status_enum", create_type=True),
            nullable=False,
        )
    )
    # ZATCA integration fields
    zatca_uuid: str | None = Field(sa_column=Column(String(255), nullable=True))
    zatca_xml: str | None = Field(sa_column=Column(pg.TEXT, nullable=True))
    zatca_xml_hash: str | None = Field(sa_column=Column(String(128), nullable=True))
    submitted_at: datetime | None = Field(sa_column=Column(pg.TIMESTAMP(timezone=True), nullable=True))
    last_error: str | None = Field(sa_column=Column(pg.TEXT, nullable=True))

    created_at: datetime = Field(sa_column=Column(pg.TIMESTAMP(timezone=True), nullable=False, default=datetime.utcnow))
    updated_at: datetime = Field(sa_column=Column(pg.TIMESTAMP(timezone=True), nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow))

    items: list["InvoiceItem"] = Relationship(back_populates="invoice", sa_relationship_kwargs={"cascade": "all, delete-orphan"})


class InvoiceItem(Base, table=True):
    __tablename__ = "invoice_item"

    id: UUID = Field(
        sa_column=Column(pg.UUID, primary_key=True, unique=True, default=uuid4)
    )
    item_name: str = Field(sa_column=Column(String(255), nullable=False))
    quantity: int = Field(sa_column=Column(pg.INTEGER, nullable=False))
    price: Decimal = Field(sa_column=Column(pg.NUMERIC(10, 2), nullable=False))
    tax: Decimal = Field(sa_column=Column(pg.NUMERIC(10, 2), nullable=False))

    invoice_id: UUID = Field(
        sa_column=Column(pg.UUID, ForeignKey("invoices.id", ondelete="CASCADE"), nullable=False)
    )

    invoice: Invoice = Relationship(back_populates="items")