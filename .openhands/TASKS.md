# Task List

1. ✅ Assess repository and confirm requirements
No src/test directory found. Existing FastAPI backend and React frontend. Invoices model exists; /invoices/count route present. Scripts and CSV data present. Several infrastructure gaps.
2. ✅ Create feature branch
Created feat/zakat-integration
3. 🔄 Fix DB async engine and add CORS

4. ⏳ Extend Invoice model to include rec_no and prepare schemas

5. ⏳ Implement importer service to load invoices from src/scripts/data

6. ⏳ Add API endpoints: import from scripts, stats for all statuses and per-status, ZATCA upload stub

7. ⏳ Create DBISAM import service and route to load root /data into secondary database

8. ⏳ Wire frontend Dashboard to backend: buttons for import, stats, ZATCA upload, DBISAM import

9. ⏳ Adjust frontend dev server to ports 12000/12001 and host settings

10. ⏳ Add minimal tests and READMEs for frontend and backend

11. ⏳ Run app locally to verify endpoints and UI

12. ⏳ Commit and push to new branch


