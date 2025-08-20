from pydantic import BaseModel, Field
from datetime import datetime
from decimal import Decimal
from uuid import UUID
from typing import List
from src.db.models.invoices import InvoiceStatus

class InvoiceItemOut(BaseModel):
    id: UUID
    item_name: str
    quantity: int
    price: Decimal
    tax: Decimal

    class Config:
        from_attributes = True

class InvoiceOut(BaseModel):
    id: UUID
    invoice_number: str
    store_name: str
    store_address: str
    vat_number: str
    date: datetime
    total: Decimal
    taxes: Decimal
    seller_taxes: Decimal
    net_total: Decimal
    user_name: str
    account_id: str
    status: InvoiceStatus
    items: List[InvoiceItemOut] = Field(default_factory=list)

    class Config:
        from_attributes = True

class CountOut(BaseModel):
    invoices_status: str
    count: int

class ImportResult(BaseModel):
    inserted: int

class ZakatUploadResult(BaseModel):
    status: str

class ZakatProcessResult(BaseModel):
    processed: int
    success: int
    failed: int
