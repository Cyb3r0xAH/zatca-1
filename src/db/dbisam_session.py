from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, AsyncEngine
from sqlalchemy.orm import sessionmaker
from src.core.config import Config
from src.db.base import Base

# Separate database for DBISAM raw data import
if not Config.DBISAM_DB_URL:
    # Fallback to main DB URL but in practice user should set DBISAM_DB_URL to a different DB
    DBISAM_URL = Config.DB_URL
else:
    DBISAM_URL = Config.DBISAM_DB_URL

engine_dbisam: AsyncEngine = create_async_engine(
    DBISAM_URL,
    echo=True,
    future=True,
)

async def init_dbisam():
    async with engine_dbisam.begin() as conn:
        from src.db.models.dbisam import DBIsamAccount, DBIsamEntry, DBIsamIndexEntry, DBIsamItem  # noqa: F401
        await conn.run_sync(Base.metadata.create_all)

async def get_dbisam_session() -> AsyncSession:
    Session = sessionmaker(
        bind=engine_dbisam,
        class_=AsyncSession,
        expire_on_commit=False,
        autoflush=False,
        autocommit=False,
    )
    async with Session() as session:
        yield session
