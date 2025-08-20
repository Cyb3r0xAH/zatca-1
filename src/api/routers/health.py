from fastapi import APIRouter
from src.services.zatca_production import get_zatca_service

router = APIRouter()

@router.get("/health", tags=["health"])
def health():
    return {"status": "ok"}

@router.get("/health/zatca", tags=["health"])
async def zatca_health_check():
    """Check ZATCA API connectivity and authentication"""
    zatca_service = get_zatca_service()
    health_status = await zatca_service.health_check()
    return health_status
