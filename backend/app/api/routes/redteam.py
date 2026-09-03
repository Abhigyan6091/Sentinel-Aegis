from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.identity import RequestIdentity
from app.core.security import get_current_identity
from app.db.session import get_session
from app.redteam.attacks import AttackGenerator, AttackSeed
from app.redteam.runner import BenchmarkRunner, CampaignRunner, campaign_store
from app.schemas.redteam import BenchmarkCreate, BenchmarkResponse, CampaignCreate, CampaignRunResponse

router = APIRouter(prefix="/red-team", tags=["red-team"])
CurrentIdentity = Annotated[RequestIdentity, Depends(get_current_identity)]
DatabaseSession = Annotated[AsyncSession, Depends(get_session)]


@router.get("/attacks", response_model=list[AttackSeed])
async def list_attack_catalog(identity: CurrentIdentity) -> list[AttackSeed]:
    del identity
    return AttackGenerator.default().seeds


@router.post(
    "/campaigns",
    response_model=CampaignRunResponse,
    status_code=status.HTTP_201_CREATED,
)
async def run_campaign(
    payload: CampaignCreate,
    identity: CurrentIdentity,
    session: DatabaseSession,
) -> CampaignRunResponse:
    return await CampaignRunner().run(payload, identity, session)


@router.post(
    "/benchmarks",
    response_model=BenchmarkResponse,
    status_code=status.HTTP_201_CREATED,
)
async def run_benchmark(
    payload: BenchmarkCreate,
    identity: CurrentIdentity,
    session: DatabaseSession,
) -> BenchmarkResponse:
    return await BenchmarkRunner().run(payload, identity, session)


@router.get("/campaigns/latest", response_model=CampaignRunResponse)
async def get_latest_campaign(identity: CurrentIdentity) -> CampaignRunResponse:
    latest = campaign_store.latest(identity.tenant_id)
    if latest is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No campaign found")
    return latest


@router.get("/findings")
async def list_findings(identity: CurrentIdentity):
    return campaign_store.findings(identity.tenant_id)
