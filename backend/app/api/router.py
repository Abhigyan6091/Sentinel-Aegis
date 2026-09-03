from fastapi import APIRouter

from app.api.routes import health, identity

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(identity.router, prefix="/api/v1")
