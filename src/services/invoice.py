# src/services/invoice.py
from sqlalchemy import select, func
from sqlmodel.ext.asyncio.session import AsyncSession
from typing import List
from src.db.models.invoices import Invoice, InvoiceStatus

class InvoicesServices:
    async def get_invoice_count_by_status(self, session: AsyncSession, status: InvoiceStatus) -> int:
        stmt = select(func.count()).select_from(Invoice).where(Invoice.status == status)
        result = await session.execute(stmt)
        count = result.scalar_one()
        return int(count)

    async def get_all_status_counts(self, session: AsyncSession) -> dict[str, int]:
        counts: dict[str, int] = {}
        for st in InvoiceStatus:
            counts[st.value] = await self.get_invoice_count_by_status(session, st)
        return counts

    async def get_invoices(self, session: AsyncSession, limit: int = 10, offset: int = 0, status: InvoiceStatus | None = None) -> List[Invoice]:
        stmt = select(Invoice)
        if status:
            stmt = stmt.where(Invoice.status == status)
        stmt = stmt.offset(offset).limit(limit).order_by(Invoice.created_at.desc())
        result = await session.execute(stmt)
        return list(result.scalars().all())
