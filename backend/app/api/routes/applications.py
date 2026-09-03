from fastapi import APIRouter, Depends, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.identity import RequestIdentity
from app.core.security import get_current_identity
from app.db.session import get_session
from app.models.foundation import Application
from app.schemas.applications import ApplicationCreate, ApplicationRead

router = APIRouter(prefix="/applications", tags=["applications"])


@router.get("", response_model=list[ApplicationRead])
async def list_applications(
    identity: RequestIdentity = Depends(get_current_identity),
    session: AsyncSession = Depends(get_session),
) -> list[Application]:
    result = await session.scalars(
        select(Application)
        .where(Application.tenant_id == identity.tenant_id)
        .order_by(Application.created_at.desc())
    )
    return list(result)


@router.post("", response_model=ApplicationRead, status_code=status.HTTP_201_CREATED)
async def create_application(
    payload: ApplicationCreate,
    identity: RequestIdentity = Depends(get_current_identity),
    session: AsyncSession = Depends(get_session),
) -> Application:
    application = Application(
        tenant_id=identity.tenant_id,
        name=payload.name,
        description=payload.description,
    )
    session.add(application)
    await session.commit()
    await session.refresh(application)
    return application
