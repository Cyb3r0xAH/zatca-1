# Task List

1. ✅ Confirm repository structure and requirements
No src/test folder. Existing FastAPI backend, React frontend. CSV import and stats endpoints exist. ZATCA upload stub present.
2. ✅ Create feature branch for changes
Created feat/zakat-integration
3. 🔄 Implement ZakatService to build/sign XML and process pending invoices
Added src/services/zakat.py; extended Invoice model with ZATCA fields; added /api/invoices/zakat/process endpoint and schemas.
4. ✅ Update API schemas and invoices router to expose /invoices/zakat/upload
Replaced with /invoices/zakat/process supporting simulate flag and limit.
5. ✅ Add frontend button to trigger ZATCA upload and display results
Dashboard now has 'معالجة زاتكا' card calling POST /api/invoices/zakat/process?simulate=true.
6. 🔄 Add basic tests for endpoints and services (skipped without DB)
Added tests/test_invoices.py with basic API tests using in-memory sqlite.
7. ✅ Update backend and frontend READMEs with instructions
Updated both READMEs with new endpoint and instructions.
8. ⏳ Run quick lint/build frontend, run backend smoke, verify endpoints

9. ⏳ Commit and push changes to new branch


