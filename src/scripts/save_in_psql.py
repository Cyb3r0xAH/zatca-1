import os
import pandas as pd
from src.scripts.invoice_id import InvoiceNumberGenerator
from src.scripts.tax_calc import tax_calc
from src.scripts.invoice_creator import InvoiceCreator
folder_path = os.path.join(os.getcwd(), 'src/scripts/data')
print(f"Using data folder: {folder_path}")

inovice_id = InvoiceNumberGenerator()
invoice_creator = InvoiceCreator()

ACCOUNTS_CSV = os.path.join(folder_path, 'Accounts-acctab.csv')
ENTRY_TAP_CSV = os.path.join(folder_path, 'EntryTab.csv')
INDEX_ENTRY_TAP_CSV = os.path.join(folder_path, 'IndexEntry.csv')
ITEMS_CSV = os.path.join(folder_path, 'Items.csv')

store = {
    "name": "شــركــة الـسـلـوم والــغيث لتسويق الـتـمـور",
    "address": "المملكة العربية السعودية - الــقــصــيــم - بريدة",
    "vat_number": "302008893200003"
}

_TRY_ENCODINGS = ("utf-8-sig", "cp1256", "latin-1")
ENDEAVOUR_TAX_RATIO = 0.15

def read_csv_with_fallback(file_path, columns=None):
    for encoding in _TRY_ENCODINGS:
        try:
            return pd.read_csv(file_path, usecols=columns, encoding=encoding)
        except Exception as e:
            print(f"Failed to read {file_path} with encoding {encoding}: {e}")
    raise RuntimeError(f"Could not read {file_path} with any of the tried encodings.")

# Items as dict: {ItemNo: ItemName}
items_df = read_csv_with_fallback(ITEMS_CSV, columns=["ItemNo", "ItemName"])
items = dict(zip(items_df["ItemNo"], items_df["ItemName"]))

# Entries as list of dicts
entries = []
entry_df = read_csv_with_fallback(ENTRY_TAP_CSV, columns=["AccNo", "AmntDB", "ItemNo", "ItemAmnt", "ItemCont"])
for _, row in entry_df.iterrows():
    entry = {
        "account_num": int(row["AccNo"]) if pd.notna(row["AccNo"]) else None,
        "total_amount": float(row["AmntDB"]),
        "item_num": float(row["ItemNo"]),
        "item_price": float(row["ItemAmnt"]),
        "item_quantity": float(row["ItemCont"]),
        "item_name": items.get(row["ItemNo"], "Unknown Item")
    }
    entries.append(entry)

indexes = []
index_df = read_csv_with_fallback(INDEX_ENTRY_TAP_CSV, columns=["RecNo", "DocKnd", "AccNo", "MDate", "Ratio", 'UserName'])
for _, row in index_df.iterrows():
    index = {
        "rec_no": int(row["RecNo"]),
        "doc_kind": int(row["DocKnd"]),
        "account_num": int(row["AccNo"]) if pd.notna(row["AccNo"]) else None,
        "date": row["MDate"],
        "ratio": float(row["Ratio"]),
        "user_name": row["UserName"] if pd.notna(row["UserName"]) else "Unknown User"
    }
    indexes.append(index)

accounts = {}
accounts_df = read_csv_with_fallback(ACCOUNTS_CSV, columns=["AccNo", "AccName"])
for _, row in accounts_df.iterrows():
    acc_no = int(row["AccNo"]) if pd. notna(row["AccNo"]) else None
    account = {
        "account_num": acc_no,
        "account_name": row["AccName"]
    }
    accounts[acc_no] = account
    
checked_accounts = []
for entry in entries:
    if entry['account_num'] in checked_accounts:
        continue
    if entry['item_name'] == "Unknown Item":
        continue
    
    account_name = accounts.get(entry['account_num'])['account_name'] if entry['account_num'] in accounts else "Unknown Account"
    for inx, entry['account_num'] in enumerate(indexes):
        store_name = store['name']
        store_address = store['address']
        store_vat_number = store['vat_number']
        account_id = entry['account_num']
        user_name = indexes[inx]['user_name']
        invoice_num = indexes[inx]['rec_no']
        date = indexes[inx]['date']
        inv = inovice_id.generate_invoice_number(invoice_num, date.replace("/", ""))
        num, uuid = inv['num'], inv['uuid']
        total = entry['total_amount']
        tax, seller_tax, net_total = tax_calc(total, indexes[inx]['ratio']/100, ENDEAVOUR_TAX_RATIO)
        data = {
            "store": {
                "name": store_name,
                "address": store_address,
                "vat_number": store_vat_number,
                "seller_number": indexes[inx]['account_num']
            },
            "invoice": {
                "number": num,
                "tax_number": num,
                "date": date
            },
            "customer": {
                "name": account_name,
                "address": account_name
            },
            "items": [
                {
                    "name": entry['item_name'],
                    "quantity": entry['item_quantity'],
                    "price": entry['item_price'],
                    "tax": tax,
                    "total": net_total
                }
            ],
            "price": {
                "subtotal": total,
                "taxes": seller_tax,
                "net_total": net_total
            }
        }
        invoice_creator.main(data, issue_datetime=date)
        break
    break

    checked_accounts.append(entry['account_num'])