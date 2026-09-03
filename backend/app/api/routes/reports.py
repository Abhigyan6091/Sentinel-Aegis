from typing import Annotated, Literal

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import PlainTextResponse

from app.core.identity import RequestIdentity
from app.core.security import get_current_identity
from app.redteam.runner import campaign_store
from app.reports.artifacts import ArtifactRecord, ArtifactStore
from app.reports.service import (
    campaign_from_report,
    campaign_report_markdown,
    campaign_report_payload,
)
from app.schemas.redteam import CampaignRunResponse

router = APIRouter(prefix="/reports", tags=["reports"])
CurrentIdentity = Annotated[RequestIdentity, Depends(get_current_identity)]
ReportFormat = Literal["json", "markdown"]


def _load_campaign(identity: RequestIdentity, campaign_id: str) -> CampaignRunResponse:
    campaign = (
        campaign_store.latest(identity.tenant_id)
        if campaign_id == "latest"
        else campaign_store.get(identity.tenant_id, campaign_id)
    )
    if campaign is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Campaign report not found",
        )
    return campaign


@router.get("/campaigns/{campaign_id}")
async def get_campaign_report_route(
    campaign_id: str,
    identity: CurrentIdentity,
    format: Annotated[ReportFormat, Query()] = "json",
    store_artifact: Annotated[bool, Query()] = False,
):
    campaign = _load_campaign(identity, campaign_id)
    if format == "markdown":
        markdown = campaign_report_markdown(campaign)
        if store_artifact:
            ArtifactStore().write(
                f"campaign-{campaign.campaign.campaign_id}.md",
                markdown,
            )
        return PlainTextResponse(markdown, media_type="text/markdown")
    return campaign_report_payload(campaign)


@router.post("/import", response_model=CampaignRunResponse)
async def import_campaign_report_route(
    payload: dict,
    identity: CurrentIdentity,
    persist: Annotated[bool, Query()] = False,
) -> CampaignRunResponse:
    """Rebuild a campaign from an exported JSON report so reports stay reproducible."""
    try:
        campaign = campaign_from_report(payload)
    except (ValueError, KeyError) as error:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid campaign report: {error}",
        ) from error

    if campaign.campaign.tenant_id != identity.tenant_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Report belongs to another tenant",
        )
    if persist:
        campaign_store.add(identity.tenant_id, campaign)
    return campaign


@router.get("/artifacts", response_model=list[ArtifactRecord])
async def list_artifacts_route(identity: CurrentIdentity) -> list[ArtifactRecord]:
    del identity
    return ArtifactStore().list()


@router.get("/artifacts/{name}", response_class=PlainTextResponse)
async def read_artifact_route(name: str, identity: CurrentIdentity) -> PlainTextResponse:
    del identity
    try:
        content = ArtifactStore().read(name)
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error),
        ) from error
    if content is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Artifact not found")
    return PlainTextResponse(content, media_type="text/markdown")
