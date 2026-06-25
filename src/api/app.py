"""FastAPI application entry point for the Baligh backend.

This module creates the FastAPI instance, registers router modules, and
manages the lifecycle of a Motor (async MongoDB) client. The client is
made available to route handlers via a FastAPI dependency.
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from motor.motor_asyncio import AsyncIOMotorClient

from .config import settings
from .routers import analysis, corrections, drafts, suggestions, tashkeel


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan manager for the FastAPI application."""
    client: AsyncIOMotorClient = AsyncIOMotorClient(settings.mongodb_uri)
    db = client.get_default_database()

    if "drafts" not in await db.list_collection_names():
        await db.create_collection("drafts")

    await db["drafts"].create_index("id", unique=True)
    await db["drafts"].create_index("revision")
    app.state.mongo_client = client
    yield
    client.close()


app = FastAPI(
    title="Baligh API",
    description="FastAPI backend for Baligh application",
    version="0.1.0",
    lifespan=lifespan,
)


app.include_router(drafts.router, prefix="/api/v1/drafts", tags=["drafts"])
app.include_router(analysis.router, prefix="/api/v1/drafts", tags=["analysis"])
app.include_router(corrections.router, prefix="/api/v1/drafts", tags=["corrections"])
app.include_router(suggestions.router, prefix="/api/v1/drafts", tags=["suggestions"])
app.include_router(tashkeel.router, prefix="/api/v1/drafts", tags=["tashkeel"])
