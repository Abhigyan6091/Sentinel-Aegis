from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.identity import RequestIdentity
from app.models.foundation import RagChunk, RagDocument
from app.rag.embeddings import DeterministicEmbeddingProvider
from app.rag.vector_store import VectorPoint, VectorStore, get_vector_store
from app.schemas.rag import RagDocumentIngest, RagSearchRequest, RagSearchResult


class RagService:
    def __init__(
        self,
        session: AsyncSession,
        embedding_provider: DeterministicEmbeddingProvider | None = None,
        vector_store: VectorStore | None = None,
    ) -> None:
        settings = get_settings()
        self.session = session
        self.embedding_provider = embedding_provider or DeterministicEmbeddingProvider(
            dimensions=settings.embedding_dimensions
        )
        self.vector_store = vector_store or get_vector_store()

    async def ingest_document(
        self,
        payload: RagDocumentIngest,
        identity: RequestIdentity,
    ) -> tuple[RagDocument, list[RagChunk]]:
        document = RagDocument(
            tenant_id=identity.tenant_id,
            application_id=payload.application_id or identity.application_id,
            source=payload.source,
            content=payload.content,
            trust_score=payload.trust_score,
            sensitivity=payload.sensitivity,
            metadata_=payload.metadata,
        )
        self.session.add(document)
        await self.session.flush()

        chunks: list[RagChunk] = []
        points: list[VectorPoint] = []
        for index, content in enumerate(chunk_text(payload.content)):
            chunk = RagChunk(
                tenant_id=identity.tenant_id,
                document_id=document.id,
                application_id=document.application_id,
                source=payload.source,
                content=content,
                chunk_index=index,
                embedding_model=self.embedding_provider.model_name,
                trust_score=payload.trust_score,
                sensitivity=payload.sensitivity,
                metadata_=payload.metadata,
            )
            self.session.add(chunk)
            await self.session.flush()
            chunks.append(chunk)
            points.append(
                VectorPoint(
                    point_id=chunk.id,
                    vector=await self.embedding_provider.embed(content),
                    payload={
                        "tenant_id": identity.tenant_id,
                        "document_id": document.id,
                        "application_id": document.application_id,
                        "source": payload.source,
                    },
                )
            )

        await self.vector_store.upsert(points)
        await self.session.commit()
        await self.session.refresh(document)
        return document, chunks

    async def search(
        self,
        payload: RagSearchRequest,
        identity: RequestIdentity,
    ) -> list[RagSearchResult]:
        vector = await self.embedding_provider.embed(payload.query)
        matches = await self.vector_store.search(vector, identity.tenant_id, payload.limit)
        if not matches:
            return []

        score_by_id = {match.point_id: match.score for match in matches}
        chunks = await self.session.scalars(
            select(RagChunk).where(
                RagChunk.id.in_(score_by_id),
                RagChunk.tenant_id == identity.tenant_id,
            )
        )
        results = [
            RagSearchResult(
                chunk_id=chunk.id,
                document_id=chunk.document_id,
                source=chunk.source,
                content=chunk.content,
                score=score_by_id[chunk.id],
                tenant_id=chunk.tenant_id,
                trust_score=chunk.trust_score,
                sensitivity=chunk.sensitivity,
                metadata=chunk.metadata_,
            )
            for chunk in chunks
            if payload.application_id is None or chunk.application_id == payload.application_id
        ]
        return sorted(results, key=lambda item: item.score, reverse=True)[: payload.limit]


def chunk_text(text: str) -> list[str]:
    settings = get_settings()
    size = settings.rag_chunk_size
    overlap = min(settings.rag_chunk_overlap, max(0, size - 1))
    if len(text) <= size:
        return [text]

    chunks: list[str] = []
    start = 0
    while start < len(text):
        chunk = text[start : start + size].strip()
        if chunk:
            chunks.append(chunk)
        start += size - overlap
    return chunks


class IngestedRagRetriever:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def retrieve(self, query: str, tenant_id: str) -> list[dict]:
        identity = RequestIdentity(
            request_id="rag-retrieval",
            user_id="system",
            tenant_id=tenant_id,
            roles=["system"],
        )
        results = await RagService(self.session).search(
            RagSearchRequest(query=query, limit=3),
            identity,
        )
        return [
            {
                "document_id": result.document_id,
                "source": result.source,
                "tenant_id": result.tenant_id,
                "trust_score": result.trust_score,
                "sensitivity": result.sensitivity,
                "content": result.content,
            }
            for result in results
        ]
