from fastapi import APIRouter

from app.api.v1.endpoints import analytics, events

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(events.router)
api_router.include_router(analytics.router)
