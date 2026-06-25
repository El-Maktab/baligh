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
    app.state.mongo_client = AsyncIOMotorClient(settings.mongodb_uri)

    yield

    app.state.mongo_client.close()


app = FastAPI(
    title="Baligh API",
    description="FastAPI backend for Baligh application",
    version="0.1.0",
    lifespan=lifespan,
)


def get_db() -> AsyncIOMotorClient:
    """Dependency that provides the Motor client.

    All routers import this dependency to interact with the ``drafts``
    collection. Using ``Depends`` ensures that FastAPI resolves the client
    lazily for each request.
    """
    return app.state.mongo_client


app.include_router(drafts.router, prefix="/api/v1/drafts", tags=["drafts"])
app.include_router(analysis.router, prefix="/api/v1/drafts", tags=["analysis"])
app.include_router(corrections.router, prefix="/api/v1/drafts", tags=["corrections"])
app.include_router(suggestions.router, prefix="/api/v1/drafts", tags=["suggestions"])
app.include_router(tashkeel.router, prefix="/api/v1/drafts", tags=["tashkeel"])
