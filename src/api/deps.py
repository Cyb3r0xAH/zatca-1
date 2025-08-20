from typing import AsyncGenerator
from src.db.session import get_session
from sqlmodel.ext.asyncio.session import AsyncSession

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async for s in get_session():
        yield s
