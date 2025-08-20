ZATCA Bridge - Backend & Frontend
by: Mohmed Mostafa

Overview
A FastAPI (backend) + React/Vite (frontend) web system for:
- Importing invoices from CSV files into a PostgreSQL database
- Counting invoices by status and returning overall stats
- Stubbing ZATCA API upload endpoint (XML + encryption to be added)
- Optional: Importing legacy DBISAM-like CSVs into a separate database

Run locally
1) Backend
- Requirements: Python 3.12+, PostgreSQL, virtualenv recommended
- Create .env in project root with at least:
  DB_URL=postgresql+asyncpg://user:pass@localhost:5432/zatca
  JWT_SECRET=dev
  STORE_NAME=Your Store
  STORE_ADDRESS=Some Address
  STORE_VAT_NUMBER=123456789
  # Optional separate DB for DBISAM raw import
  # DBISAM_DB_URL=postgresql+asyncpg://user:pass@localhost:5432/zatca_raw

Install deps and run API on port 12000:
  pip install -r requirements.txt
  uvicorn src:app --host 0.0.0.0 --port 12000 --reload

API base: /api
Main endpoints:
- POST /api/invoices/import  -> import invoices from src/scripts/data (inserts only new RecNo)
- GET  /api/invoices/stats   -> status map {pending, in_progress, done, failed}
- GET  /api/invoices/count?status=pending -> single status count
- POST /api/invoices/zakat/process -> processes PENDING invoices: build XML, base64+hash, simulate upload (or real if ZATCA_ENDPOINT set)

2) Frontend
From frontend/ directory:
  npm install
  npm run dev
Vite dev runs at 12001 and proxies /api to http://localhost:12000

Data locations
- src/scripts/data: source CSVs (Items.csv, EntryTab.csv, IndexEntry.csv)
- data/: optional root-level CSVs for DBISAM import (acctab.csv, items.csv, entrytab.csv, indexentry.csv)

Optional DBISAM import
- A separate async engine is provided (src/db/dbisam_session.py)
- Service to import root data into that DB: src/services/dbisam_importer.py
  You can wire an endpoint later to run it on demand.

Testing
- pytest is configured; run pytest to execute tests under tests/

Notes
- CORS enabled for development
- Async SQLAlchemy/SQLModel engine and sessions are used
- ZATCA upload endpoint is a stub; provide certs/keys in .env once implementing
