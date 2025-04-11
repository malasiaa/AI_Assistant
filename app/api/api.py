from fastapi import APIRouter
from app.api.v1.endpoints import notes, calendar, actions

api_router = APIRouter()
api_router.include_router(notes.router, prefix="/notes", tags=["Notes"])
api_router.include_router(calendar.router, prefix="/calendar", tags=["Calendar"])
api_router.include_router(actions.router, prefix="/actions", tags=["Actions"])
