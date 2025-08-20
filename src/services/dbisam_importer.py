import os
import pandas as pd
from sqlmodel.ext.asyncio.session import AsyncSession
from src.db.models.dbisam import DBIsamAccount, DBIsamEntry, DBIsamIndexEntry, DBIsamItem

# Get the project root directory (where this file is located)
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
ROOT_DATA_DIR = os.path.join(PROJECT_ROOT, 'data')
TRY_ENCODINGS = ("utf-8-sig", "cp1256", "latin-1")

class DBISAMImportService:
    def _read_csv(self, file_path: str, columns=None, header=None) -> pd.DataFrame:
        for enc in TRY_ENCODINGS:
            try:
                return pd.read_csv(file_path, usecols=columns, encoding=enc, header=header)
            except Exception:
                continue
        raise RuntimeError(f"Unable to read: {file_path}")

    def _safe_float(self, value, default=0.0):
        """Safely convert value to float, handling empty strings and non-numeric values"""
        try:
            if pd.isna(value) or value == '' or value is None:
                return default
            return float(value)
        except (ValueError, TypeError):
            return default

    def _safe_int(self, value, default=0):
        """Safely convert value to int, handling empty strings and non-numeric values"""
        try:
            if pd.isna(value) or value == '' or value is None:
                return default
            return int(float(value))  # Convert to float first to handle decimal strings
        except (ValueError, TypeError):
            return default

    async def import_all(self, session: AsyncSession) -> dict[str, int]:
        stats = {"accounts": 0, "items": 0, "entries": 0, "index_entries": 0}

        # Read accounts CSV without headers, assuming first column is AccNo, fourth is AccName
        accounts_file = os.path.join(ROOT_DATA_DIR, 'acctab.csv')
        if os.path.exists(accounts_file):
            try:
                accounts = self._read_csv(accounts_file, columns=[0, 3], header=None)  # type: ignore
                accounts.columns = ["AccNo", "AccName"]
                for _, r in accounts.iterrows():
                    session.add(DBIsamAccount(acc_no=str(r["AccNo"]), acc_name=str(r["AccName"])) )
                    stats["accounts"] += 1
            except Exception as e:
                print(f"Error importing accounts: {e}")

        # Read items CSV without headers
        items_file = os.path.join(ROOT_DATA_DIR, 'itemstab.csv')
        if os.path.exists(items_file):
            try:
                items = self._read_csv(items_file, header=None)  # type: ignore
                # Assume first two columns are ItemNo and ItemName
                if len(items.columns) >= 2:
                    items.columns = ["ItemNo", "ItemName"] + [f"col_{i}" for i in range(2, len(items.columns))]
                    for _, r in items.iterrows():
                        session.add(DBIsamItem(item_no=str(r["ItemNo"]), item_name=str(r["ItemName"])) )
                        stats["items"] += 1
            except Exception as e:
                print(f"Error importing items: {e}")

        # Read entries CSV without headers - based on actual structure from sample
        entries_file = os.path.join(ROOT_DATA_DIR, 'entrytab.csv')
        if os.path.exists(entries_file):
            try:
                entries = self._read_csv(entries_file, header=None)  # type: ignore
                # Based on sample: RecId, ?, ?, AccNo, AmntDB, ItemAmnt, ?, ?, ?, ItemCont/Description
                if len(entries.columns) >= 6:
                    for _, r in entries.iterrows():
                        session.add(DBIsamEntry(
                            rec_id=self._safe_int(r.iloc[0]), 
                            acc_no=str(r.iloc[3] if len(r) > 3 else ""), 
                            amnt_db=self._safe_float(r.iloc[4] if len(r) > 4 else 0), 
                            item_no=str(r.iloc[3] if len(r) > 3 else ""),  # Using AccNo as ItemNo for now
                            item_amnt=self._safe_float(r.iloc[5] if len(r) > 5 else 0), 
                            item_cont=self._safe_float(r.iloc[6] if len(r) > 6 else 0)
                        ))
                        stats["entries"] += 1
            except Exception as e:
                print(f"Error importing entries: {e}")

        # Read index entries CSV without headers
        index_file = os.path.join(ROOT_DATA_DIR, 'indexentrytab.csv')
        if os.path.exists(index_file):
            try:
                index = self._read_csv(index_file, header=None)  # type: ignore
                # Map columns based on expected structure
                if len(index.columns) >= 7:
                    for _, r in index.iterrows():
                        session.add(DBIsamIndexEntry(
                            rec_no=self._safe_int(r.iloc[0]), 
                            doc_no=self._safe_int(r.iloc[1] if len(r) > 1 else 0), 
                            doc_knd=self._safe_int(r.iloc[2] if len(r) > 2 else 0), 
                            acc_no=str(r.iloc[3] if len(r) > 3 else ""), 
                            mdate=str(r.iloc[4] if len(r) > 4 else ""), 
                            ratio=self._safe_float(r.iloc[5] if len(r) > 5 else 0), 
                            username=str(r.iloc[6] if len(r) > 6 else "")
                        ))
                        stats["index_entries"] += 1
            except Exception as e:
                print(f"Error importing index entries: {e}")

        await session.commit()
        return stats
