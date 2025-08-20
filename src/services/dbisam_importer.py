import os
import pandas as pd
from sqlmodel.ext.asyncio.session import AsyncSession
from src.db.models.dbisam import DBIsamAccount, DBIsamEntry, DBIsamIndexEntry, DBIsamItem

ROOT_DATA_DIR = os.path.join(os.getcwd(), 'data')
TRY_ENCODINGS = ("utf-8-sig", "cp1256", "latin-1")

class DBISAMImportService:
    def _read_csv(self, file_path: str, columns=None) -> pd.DataFrame:
        for enc in TRY_ENCODINGS:
            try:
                return pd.read_csv(file_path, usecols=columns, encoding=enc)
            except Exception:
                continue
        raise RuntimeError(f"Unable to read: {file_path}")

    async def import_all(self, session: AsyncSession) -> dict[str, int]:
        stats = {"accounts": 0, "items": 0, "entries": 0, "index_entries": 0}

        accounts = self._read_csv(os.path.join(ROOT_DATA_DIR, 'acctab.csv'), columns=["AccNo", "AccName"])  # type: ignore
        for _, r in accounts.iterrows():
            session.add(DBIsamAccount(acc_no=str(r["AccNo"]), acc_name=str(r["AccName"])) )
            stats["accounts"] += 1

        items = self._read_csv(os.path.join(ROOT_DATA_DIR, 'items.csv'), columns=["ItemNo", "ItemName"])  # type: ignore
        for _, r in items.iterrows():
            session.add(DBIsamItem(item_no=str(r["ItemNo"]), item_name=str(r["ItemName"])) )
            stats["items"] += 1

        entries = self._read_csv(os.path.join(ROOT_DATA_DIR, 'entrytab.csv'), columns=["RecId", "AccNo", "AmntDB", "ItemNo", "ItemAmnt", "ItemCont"])  # type: ignore
        for _, r in entries.iterrows():
            session.add(DBIsamEntry(rec_id=int(r["RecId"]), acc_no=str(r["AccNo"]), amnt_db=float(r["AmntDB"] or 0.0), item_no=str(r.get("ItemNo", "") or ""), item_amnt=float(r.get("ItemAmnt", 0.0) or 0.0), item_cont=float(r.get("ItemCont", 0.0) or 0.0)))
            stats["entries"] += 1

        index = self._read_csv(os.path.join(ROOT_DATA_DIR, 'indexentry.csv'), columns=["RecNo", "DocNo", "DocKnd", "AccNo", "MDate", "Ratio", "UserName"])  # type: ignore
        for _, r in index.iterrows():
            session.add(DBIsamIndexEntry(rec_no=int(r["RecNo"]), doc_no=int(r.get("DocNo", 0) or 0), doc_knd=int(r.get("DocKnd", 0) or 0), acc_no=str(r.get("AccNo", "") or ""), mdate=str(r.get("MDate", "") or ""), ratio=float(r.get("Ratio", 0.0) or 0.0), username=str(r.get("UserName", "") or "")))
            stats["index_entries"] += 1

        await session.commit()
        return stats
