from fastapi import APIRouter

from app.api.routes import applications, health, identity, redteam, support

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(identity.router, prefix="/api/v1")
api_router.include_router(applications.router, prefix="/api/v1")
api_router.include_router(support.router, prefix="/api/v1")
api_router.include_router(redteam.router, prefix="/api/v1")
