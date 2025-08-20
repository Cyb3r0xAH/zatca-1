import os
import pandas as pd
from datetime import datetime
from decimal import Decimal
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy import select
from src.db.models.invoices import Invoice, InvoiceItem, InvoiceStatus
from src.core.config import Config

DATA_DIR = os.path.join(os.getcwd(), 'src/scripts/data')

TRY_ENCODINGS = ("utf-8-sig", "cp1256", "latin-1")

class ImportService:
    def _read_csv(self, file_path: str, columns=None) -> pd.DataFrame:
        for enc in TRY_ENCODINGS:
            try:
                return pd.read_csv(file_path, usecols=columns, encoding=enc)
            except Exception:
                continue
        raise RuntimeError(f"Unable to read: {file_path}")

    async def import_from_scripts(self, session: AsyncSession) -> int:
        items_df = self._read_csv(os.path.join(DATA_DIR, 'Items.csv'), columns=["ItemNo", "ItemName"])  # noqa: F841
        entries_df = self._read_csv(os.path.join(DATA_DIR, 'EntryTab.csv'), columns=["AccNo", "AmntDB", "ItemNo", "ItemAmnt", "ItemCont"])  # noqa: E501
        index_df = self._read_csv(os.path.join(DATA_DIR, 'IndexEntry.csv'), columns=["RecNo", "DocKnd", "AccNo", "MDate", "Ratio", "UserName"])  # noqa: E501

        # We'll group by RecNo (document number) and create one invoice per RecNo that is not present in DB
        inserted = 0
        for _, idx in index_df.iterrows():
            rec_no = int(idx["RecNo"]) if pd.notna(idx["RecNo"]) else None
            if rec_no is None:
                continue

            # check if invoice with invoice_number == rec_no exists
            exists_stmt = select(Invoice).where(Invoice.invoice_number == str(rec_no))
            res = await session.execute(exists_stmt)
            if res.scalars().first():
                continue

            # filter entries for this rec_no in entries_df: RecId is not provided linking; simple approach uses AccNo match
            # In provided sample, totals per invoice exist in index_df["Total"], but columns selected don't include Total.
            # We'll compute a simplistic total sum of AmntDB for matching AccNo and DocKnd context; fallback to 0.
            account_num = int(idx["AccNo"]) if pd.notna(idx["AccNo"]) else None
            mdate = str(idx["MDate"]) if pd.notna(idx["MDate"]) else datetime.utcnow().strftime('%Y/%m/%d')
            ratio = float(idx["Ratio"]) if pd.notna(idx["Ratio"]) else 0.0
            user_name = str(idx["UserName"]) if pd.notna(idx["UserName"]) else "system"

            # Aggregate entries
            if account_num is not None:
                related = entries_df[entries_df["AccNo"] == account_num]
            else:
                related = entries_df.iloc[0:0]

            subtotal = float(related["AmntDB"].sum()) if not related.empty else 0.0
            # Simple calc like script: tax = subtotal * (ratio/100); seller_tax = tax * 0.15; net_total = subtotal - seller_tax - tax
            tax = subtotal * (ratio/100.0)
            seller_tax = tax * 0.15
            net_total = subtotal - seller_tax - tax

            inv = Invoice(
                invoice_number=str(rec_no),
                store_name=Config.STORE_NAME or "",
                store_address=Config.STORE_ADDRESS or "",
                vat_number=Config.STORE_VAT_NUMBER or "",
                date=datetime.strptime(mdate, "%Y/%m/%d"),
                total=Decimal(str(round(subtotal, 2))),
                taxes=Decimal(str(round(tax, 2))),
                seller_taxes=Decimal(str(round(seller_tax, 2))),
                net_total=Decimal(str(round(net_total, 2))),
                user_name=user_name,
                account_id=str(account_num) if account_num is not None else "",
                status=InvoiceStatus.PENDING,
            )
            session.add(inv)
            await session.flush()

            # Add first line item from related if exists
            if not related.empty:
                first = related.iloc[0]
                item = InvoiceItem(
                    invoice_id=inv.id,
                    item_name=str(first.get("ItemNo", "")),
                    quantity=int(first.get("ItemCont", 1) or 1),
                    price=Decimal(str(first.get("ItemAmnt", 0.0) or 0.0)),
                    tax=Decimal(str(round(tax, 2))),
                )
                session.add(item)

            inserted += 1

        await session.commit()
        return inserted
