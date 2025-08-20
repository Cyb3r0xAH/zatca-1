Frontend (React + Vite)
by: Mohmed Mostafa

Run
- npm install
- npm run dev

Dev server runs on http://localhost:12001 and proxies /api to http://localhost:12000 (FastAPI backend).

Dashboard actions
- جلب البيانات: calls POST /api/invoices/import to import CSV invoices from src/scripts/data
- فحص الحالة: calls GET /api/invoices/stats to display counts by status
- معالجة زاتكا: calls POST /api/invoices/zakat/process?simulate=true to build/sign XML and upload (simulated by default)
- استيراد DBISAM: calls POST /api/dbisam/import to ingest root data/*.csv into a separate database

Notes
- Adjust proxy target in vite.config.ts if backend port changes
