# Qdrant RAG Phase 3 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add document ingestion, deterministic embeddings, vector-store retrieval, and tenant-scoped RAG APIs for Sentinel Aegis.

**Architecture:** Persist document and chunk metadata in SQLAlchemy models, generate deterministic embeddings for local/test mode, and route retrieval through a vector-store abstraction with memory and Qdrant HTTP implementations. The support agent keeps fixture retrieval by default but can use ingested RAG through settings.

**Tech Stack:** FastAPI, SQLAlchemy async, httpx, deterministic local embeddings, Qdrant-compatible HTTP abstraction, pytest.

**Spec:** `docs/production-roadmap.md` Phase P3.

## Global Constraints

- Existing fixture-based support-agent demos must continue to work by default.
- RAG ingestion and search must be tenant scoped.
- Tests must not require a running Qdrant service.
- Production deployments can select Qdrant through settings.
- Context firewall decisions must still run over retrieved content.

---

### Task 1: RAG Models And Schemas

**Files:**
- Modify: `backend/app/models/foundation.py`
- Create: `backend/app/schemas/rag.py`
- Create: `backend/alembic/versions/20260903_0002_rag_documents.py`
- Test: `backend/tests/test_rag_api.py`

**Interfaces:**
- Produces document/chunk persistence and API schemas.

- [ ] Write failing API tests for ingestion and search.
- [ ] Add models, schemas, and migration.
- [ ] Run focused tests.

### Task 2: Embeddings And Vector Store

**Files:**
- Create: `backend/app/rag/embeddings.py`
- Create: `backend/app/rag/vector_store.py`
- Create: `backend/app/rag/service.py`
- Test: `backend/tests/test_rag_api.py`

**Interfaces:**
- Produces `RagService.ingest_document(...)` and `RagService.search(...)`.

- [ ] Implement deterministic embeddings and memory vector search.
- [ ] Add Qdrant HTTP vector-store implementation.
- [ ] Run focused tests.

### Task 3: API Routes And Support-Agent Wiring

**Files:**
- Create: `backend/app/api/routes/rag.py`
- Modify: `backend/app/api/router.py`
- Modify: `backend/app/support/agent.py`
- Modify: `backend/app/core/config.py`
- Modify: `.env.example`
- Modify: `README.md`
- Modify local ignored: `summarizer.md`

- [ ] Expose `POST /api/v1/rag/documents`.
- [ ] Expose `POST /api/v1/rag/search`.
- [ ] Allow support-agent retrieval from ingested RAG when configured.
- [ ] Run full verification and commit.
