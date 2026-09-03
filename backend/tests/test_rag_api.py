import json

import httpx
import pytest
from fastapi.testclient import TestClient

from app.core.config import get_settings
from app.main import create_app
from app.rag.vector_store import QdrantVectorStore, VectorPoint


def make_client(monkeypatch, tmp_path) -> TestClient:
    monkeypatch.setenv("AEGIS_DATABASE_URL", f"sqlite+aiosqlite:///{tmp_path / 'rag.db'}")
    monkeypatch.setenv("AEGIS_RAG_VECTOR_STORE", "memory")
    get_settings.cache_clear()
    return TestClient(create_app())


def test_rag_document_ingestion_and_search(monkeypatch, tmp_path):
    client = make_client(monkeypatch, tmp_path)

    created = client.post(
        "/api/v1/rag/documents",
        headers={"x-api-key": "dev-aegis-key"},
        json={
            "source": "support-kb",
            "content": (
                "Warranty replacements require the device serial number and proof of purchase."
            ),
            "trust_score": 0.94,
            "sensitivity": "INTERNAL",
            "metadata": {"topic": "warranty"},
        },
    )
    assert created.status_code == 201
    assert created.json()["chunk_count"] == 1

    search = client.post(
        "/api/v1/rag/search",
        headers={"x-api-key": "dev-aegis-key"},
        json={"query": "warranty serial number", "limit": 3},
    )

    assert search.status_code == 200
    assert search.json()["results"][0]["source"] == "support-kb"
    assert "serial number" in search.json()["results"][0]["content"]


def test_rag_search_is_tenant_scoped(monkeypatch, tmp_path):
    client = make_client(monkeypatch, tmp_path)
    client.post(
        "/api/v1/rag/documents",
        headers={"x-api-key": "dev-aegis-key"},
        json={
            "source": "tenant-a",
            "content": "Private billing policy for tenant demo.",
            "trust_score": 0.9,
        },
    )

    other = client.post(
        "/api/v1/rag/search",
        headers={"x-api-key": "dev-other-key"},
        json={"query": "private billing policy", "limit": 3},
    )

    assert other.status_code == 200
    assert other.json()["results"] == []


def test_support_agent_can_use_ingested_rag(monkeypatch, tmp_path):
    client = make_client(monkeypatch, tmp_path)
    monkeypatch.setenv("AEGIS_SUPPORT_RETRIEVER", "rag")
    get_settings.cache_clear()

    client.post(
        "/api/v1/rag/documents",
        headers={"x-api-key": "dev-aegis-key"},
        json={
            "source": "support-kb",
            "content": "Warranty replacements require the device serial number.",
            "trust_score": 0.95,
        },
    )

    response = client.post(
        "/api/v1/support/chat",
        headers={"x-api-key": "dev-aegis-key"},
        json={"message": "What is the warranty replacement process?"},
    )

    assert response.status_code == 200
    assert "Warranty replacements require the device serial number" in response.json()["answer"]


@pytest.mark.asyncio
async def test_qdrant_vector_store_uses_tenant_filter():
    requests: list[tuple[str, dict]] = []

    async def handler(request: httpx.Request) -> httpx.Response:
        body = json.loads(request.content)
        requests.append((request.url.path, body))
        if request.method == "POST":
            return httpx.Response(200, json={"result": [{"id": "chunk-1", "score": 0.91}]})
        return httpx.Response(200, json={"result": True})

    store = QdrantVectorStore(
        url="http://qdrant",
        collection="sentinel",
        dimensions=2,
        client=httpx.AsyncClient(
            base_url="http://qdrant",
            transport=httpx.MockTransport(handler),
        ),
    )

    await store.upsert(
        [
            VectorPoint(
                point_id="chunk-1",
                vector=[1, 0],
                payload={"tenant_id": "tenant-demo"},
            )
        ]
    )
    matches = await store.search([1, 0], tenant_id="tenant-demo", limit=1)

    assert matches[0].point_id == "chunk-1"
    assert requests[-1][1]["filter"]["must"][0]["match"]["value"] == "tenant-demo"
