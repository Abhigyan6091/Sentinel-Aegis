from fastapi import APIRouter, Depends

from app.core.identity import RequestIdentity
from app.core.security import get_current_identity

router = APIRouter(tags=["identity"])


@router.get("/me", response_model=RequestIdentity)
async def read_current_identity(
    identity: RequestIdentity = Depends(get_current_identity),
) -> RequestIdentity:
    return identity
