from pydantic import BaseModel, Field


class RequestIdentity(BaseModel):
    request_id: str
    user_id: str
    tenant_id: str
    application_id: str | None = None
    roles: list[str] = Field(default_factory=list)
