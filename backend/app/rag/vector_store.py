from dataclasses import dataclass
from typing import Protocol

import httpx

from app.core.config import get_settings


@dataclass(frozen=True)
class VectorPoint:
    point_id: str
    vector: list[float]
    payload: dict


@dataclass(frozen=True)
class VectorMatch:
    point_id: str
    score: float


class VectorStore(Protocol):
    async def upsert(self, points: list[VectorPoint]) -> None:
        raise NotImplementedError

    async def search(self, vector: list[float], tenant_id: str, limit: int) -> list[VectorMatch]:
        raise NotImplementedError


class MemoryVectorStore:
    def __init__(self) -> None:
        self.points: dict[str, VectorPoint] = {}

    async def upsert(self, points: list[VectorPoint]) -> None:
        for point in points:
            self.points[point.point_id] = point

    async def search(self, vector: list[float], tenant_id: str, limit: int) -> list[VectorMatch]:
        matches = [
            VectorMatch(point_id=point.point_id, score=cosine_similarity(vector, point.vector))
            for point in self.points.values()
            if point.payload.get("tenant_id") == tenant_id
        ]
        return sorted(matches, key=lambda match: match.score, reverse=True)[:limit]


class QdrantVectorStore:
    def __init__(
        self,
        *,
        url: str,
        collection: str,
        dimensions: int,
        client: httpx.AsyncClient | None = None,
    ) -> None:
        self.collection = collection
        self.dimensions = dimensions
        self.client = client or httpx.AsyncClient(base_url=url, timeout=10)

    async def ensure_collection(self) -> None:
        response = await self.client.put(
            f"/collections/{self.collection}",
            json={"vectors": {"size": self.dimensions, "distance": "Cosine"}},
        )
        if response.status_code >= 400:
            raise RuntimeError(f"Qdrant collection setup failed with {response.status_code}")

    async def upsert(self, points: list[VectorPoint]) -> None:
        await self.ensure_collection()
        response = await self.client.put(
            f"/collections/{self.collection}/points",
            params={"wait": "true"},
            json={
                "points": [
                    {"id": point.point_id, "vector": point.vector, "payload": point.payload}
                    for point in points
                ]
            },
        )
        if response.status_code >= 400:
            raise RuntimeError(f"Qdrant upsert failed with {response.status_code}")

    async def search(self, vector: list[float], tenant_id: str, limit: int) -> list[VectorMatch]:
        await self.ensure_collection()
        response = await self.client.post(
            f"/collections/{self.collection}/points/search",
            json={
                "vector": vector,
                "limit": limit,
                "filter": {"must": [{"key": "tenant_id", "match": {"value": tenant_id}}]},
            },
        )
        if response.status_code >= 400:
            raise RuntimeError(f"Qdrant search failed with {response.status_code}")
        return [
            VectorMatch(point_id=str(item["id"]), score=float(item["score"]))
            for item in response.json().get("result", [])
        ]


_memory_store = MemoryVectorStore()


def get_vector_store() -> VectorStore:
    settings = get_settings()
    if settings.rag_vector_store == "qdrant":
        return QdrantVectorStore(
            url=settings.qdrant_url,
            collection=settings.qdrant_collection,
            dimensions=settings.embedding_dimensions,
        )
    return _memory_store


def cosine_similarity(left: list[float], right: list[float]) -> float:
    return sum(a * b for a, b in zip(left, right, strict=False))
