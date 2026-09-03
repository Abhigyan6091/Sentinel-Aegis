from datetime import datetime

from pydantic import BaseModel, Field


class ApplicationCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=2000)


class ApplicationRead(BaseModel):
    id: str
    tenant_id: str
    name: str
    description: str | None
    status: str
    created_at: datetime

    model_config = {"from_attributes": True}
