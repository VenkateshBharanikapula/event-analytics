from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.api.v1.router import api_router
from app.core.config import settings
from app.core.exceptions import (
    CategoryNotFoundException,
    DuplicateEventException,
    EventNotFoundException,
)
from app.core.logging import setup_logging
from app.integrations.redis.client import close_redis


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging(debug=settings.DEBUG)
    yield
    await close_redis()


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description=(
        "A production-ready backend for ingesting, categorizing, analyzing, "
        "and archiving application events."
    ),
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

app.include_router(api_router)


# ── Global exception handlers ────────────────────────────────────────────────

@app.exception_handler(EventNotFoundException)
async def event_not_found_handler(request: Request, exc: EventNotFoundException):
    return JSONResponse(status_code=404, content={"detail": str(exc)})


@app.exception_handler(DuplicateEventException)
async def duplicate_event_handler(request: Request, exc: DuplicateEventException):
    return JSONResponse(status_code=409, content={"detail": str(exc)})


@app.exception_handler(CategoryNotFoundException)
async def category_not_found_handler(request: Request, exc: CategoryNotFoundException):
    return JSONResponse(status_code=404, content={"detail": str(exc)})


# ── Health check ─────────────────────────────────────────────────────────────

@app.get("/health", tags=["Health"])
async def health():
    return {"status": "ok", "version": settings.APP_VERSION}
