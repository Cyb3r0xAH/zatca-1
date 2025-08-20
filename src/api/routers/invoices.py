from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel.ext.asyncio.session import AsyncSession
from typing import Dict
from src.db.models.invoices import InvoiceStatus
from src.schemas.invoices import CountOut, ZakatUploadResult, ImportResult, ZakatProcessResult
from src.db.session import get_session
from src.services.invoice import InvoicesServices
from src.services.importer import ImportService
from src.services.zakat import ZakatService

router = APIRouter(prefix='/invoices', tags=['Invoices'])

invoices_services = InvoicesServices()
import_service = ImportService()
zakat_service = ZakatService()

@router.get('/count', response_model=CountOut)
async def fetch_invoice_count(
        status: InvoiceStatus = Query(..., description="Filter invoices by status"),
        session: AsyncSession = Depends(get_session)
    ) -> Dict[str, int | str]:
    count = await invoices_services.get_invoice_count_by_status(session, status)
    return {"invoices_status": status.value, "count": count}

@router.get('/stats', response_model=dict[str, int])
async def fetch_invoice_stats(session: AsyncSession = Depends(get_session)) -> Dict[str, int]:
    return await invoices_services.get_all_status_counts(session)

@router.post('/import', response_model=ImportResult)
async def import_invoices(session: AsyncSession = Depends(get_session)) -> Dict[str, int]:
    try:
        inserted = await import_service.import_from_scripts(session)
        return {"inserted": inserted}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post('/zakat/process', response_model=ZakatProcessResult)
async def zakat_process(limit: int = Query(50), simulate: bool = Query(True), session: AsyncSession = Depends(get_session)) -> Dict[str, int]:
    try:
        return await zakat_service.process_pending(session, limit=limit, simulate=simulate)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
