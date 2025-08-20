from fastapi import APIRouter, Depends, HTTPException
from sqlmodel.ext.asyncio.session import AsyncSession
from src.db.dbisam_session import get_dbisam_session, init_dbisam
from src.services.dbisam_importer import DBISAMImportService

router = APIRouter(prefix='/dbisam', tags=['DBISAM'])

importer = DBISAMImportService()

@router.post('/import')
async def import_dbisam(session: AsyncSession = Depends(get_dbisam_session)) -> dict:
    try:
        await init_dbisam()
        stats = await importer.import_all(session)
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
