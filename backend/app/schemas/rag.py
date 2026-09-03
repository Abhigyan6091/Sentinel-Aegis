from datetime import datetime

from pydantic import BaseModel, Field


class RagDocumentIngest(BaseModel):
    source: str = Field(min_length=1, max_length=255)
    content: str = Field(min_length=1, max_length=200_000)
    application_id: str | None = None
    trust_score: float = Field(default=0.8, ge=0, le=1)
    sensitivity: str = Field(default="PUBLIC", max_length=32)
    metadata: dict[str, str] = Field(default_factory=dict)


class RagDocumentIngested(BaseModel):
    document_id: str
    chunk_count: int
    source: str
    created_at: datetime


class RagSearchRequest(BaseModel):
    query: str = Field(min_length=1, max_length=4000)
    application_id: str | None = None
    limit: int = Field(default=5, ge=1, le=20)


class RagSearchResult(BaseModel):
    chunk_id: str
    document_id: str
    source: str
    content: str
    score: float
    tenant_id: str
    trust_score: float
    sensitivity: str
    metadata: dict


class RagSearchResponse(BaseModel):
    results: list[RagSearchResult]
