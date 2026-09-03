from fastapi import APIRouter

from app.api.routes import (
    applications,
    approvals,
    findings,
    health,
    identity,
    observability,
    policies,
    rag,
    redteam,
    regression,
    reports,
    support,
)

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(observability.router)
api_router.include_router(identity.router, prefix="/api/v1")
api_router.include_router(applications.router, prefix="/api/v1")
api_router.include_router(policies.router, prefix="/api/v1")
api_router.include_router(approvals.router, prefix="/api/v1")
api_router.include_router(support.router, prefix="/api/v1")
api_router.include_router(redteam.router, prefix="/api/v1")
api_router.include_router(rag.router, prefix="/api/v1")
api_router.include_router(findings.router, prefix="/api/v1")
api_router.include_router(regression.router, prefix="/api/v1")
api_router.include_router(reports.router, prefix="/api/v1")
