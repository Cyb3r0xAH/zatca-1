# Task List

1. ✅ Explore repository, locate requirements (src/test) and current implementations
No src/test folder found. Requirements inferred from existing code, tests, and user context.
2. ✅ Fix backend test suite failures
Adjusted tests to mock DB/service methods, fixed TestClient usage, added selectinload to avoid lazy-load issues. All tests pass.
3. ✅ Clean frontend Dashboard stray JSX and validate build basics
Removed stray 'Status Data Display' block and closed Card properly.
4. ✅ Ensure dependencies include httpx
Added httpx==0.28.1 to requirements.txt
5. ✅ Align Alembic migration with Invoice model fields (invoice_number, vat_number, seller_taxes, ZATCA fields, lowercase enum)
Added new migration 8f2c0c3e1aa9 to alter invoices table and enum.
6. ✅ Verify importer only inserts invoices whose rec_no not in DB
ImportService checks existence by invoice_number; OK.
7. ⏳ Document backend/frontend (README) and endpoints
Ensure README mentions count/stats and ZATCA process. Update if needed.
8. ⏳ Commit changes and push to a feature branch
Commit with co-author, push to remote branch.

