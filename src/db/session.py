from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, AsyncEngine
from sqlalchemy.orm import sessionmaker
from src.core.config import Config
from .base import Base

# Primary application database (async)
engine: AsyncEngine = create_async_engine(
    Config.DB_URL,
    echo=True,
    future=True,
)

async def init_db():
    async with engine.begin() as conn:
        from src.db.models.accounts import Account  # noqa: F401
        from src.db.models.groups import Group  # noqa: F401
        from src.db.models.invoices import Invoice, InvoiceItem  # noqa: F401
        from src.db.models.items import Item  # noqa: F401
        from src.db.models.users import User  # noqa: F401
        await conn.run_sync(Base.metadata.create_all)

async def get_session() -> AsyncSession:
    Session = sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autoflush=False,
        autocommit=False,
    )
    async with Session() as session:
        yield session
