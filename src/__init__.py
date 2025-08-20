import logging
from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from src.core.config import Config
from src.api.routers import health, invoices, dbisam
from src.db.session import init_db

logger = logging.getLogger("uvicorn.error")


@asynccontextmanager
async def life_span(app: FastAPI) -> AsyncGenerator[None, None]:
    logger.info("Starting application lifespan: initializing DB...")
    try:
        await init_db()
        logger.info("Database initialization finished.")
    except Exception as e:
        logger.exception("Database initialization failed: %s", e)
        raise

    try:
        yield
    finally:
        logger.info("Shutting down application lifespan.")


api_str = getattr(Config, "API_STR", "/api")
prefix = getattr(Config, "PREFIX", "")

app = FastAPI(
    title="ZATCA Bridge",
    description="A System for ZATCA invoices manipulation",
    version=str(api_str),
    lifespan=life_span,
)

# Allow frontend requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

api_prefix = f"/api"
app.include_router(health.router, prefix=api_prefix)
app.include_router(invoices.router, prefix=api_prefix)
app.include_router(dbisam.router, prefix=api_prefix)
