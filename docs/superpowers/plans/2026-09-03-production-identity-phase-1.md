# Production Identity Phase 1 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add production identity foundations with issuer/audience validated JWTs, reusable role checks, and preserved local development auth.

**Architecture:** Keep existing API-key auth for local mode, but add a JWT validation path for bearer tokens. JWT validation uses configured issuer, audience, algorithms, and JWKS JSON/URL inputs, returning the existing `RequestIdentity` model so API routes do not need broad rewrites.

**Tech Stack:** FastAPI dependencies, PyJWT, cryptography-backed RS256 tests, pytest, Pydantic settings.

**Spec:** `docs/production-roadmap.md` Phase P1.

## Global Constraints

- Existing local `dev-aegis-key` and `dev-other-key` behavior must keep working by default.
- Production JWT mode must support JWKS key validation, issuer validation, audience validation, expiry validation, tenant claim, roles claim, and application claim.
- Disabling development API keys must reject API-key credentials.
- Role authorization must return HTTP 403 for missing roles.

---

### Task 1: JWT Settings And Validation

**Files:**
- Modify: `backend/app/core/config.py`
- Modify: `backend/app/core/security.py`
- Modify: `backend/pyproject.toml`
- Test: `backend/tests/test_jwt_auth.py`

**Interfaces:**
- Produces: JWT bearer authentication through `get_current_identity`.

- [ ] Write tests for valid RS256 JWT, invalid issuer, and disabled development API keys.
- [ ] Run `python3 -m pytest tests/test_jwt_auth.py -q` and confirm failures.
- [ ] Add settings and validation implementation.
- [ ] Run the focused tests and confirm pass.

### Task 2: Role Authorization Helper

**Files:**
- Modify: `backend/app/core/security.py`
- Test: `backend/tests/test_jwt_auth.py`

**Interfaces:**
- Produces: `require_any_role(identity: RequestIdentity, allowed_roles: set[str]) -> RequestIdentity`.

- [ ] Add tests proving allowed roles pass and missing roles raise 403.
- [ ] Implement the helper.
- [ ] Run the focused tests and confirm pass.

### Task 3: Documentation And Verification

**Files:**
- Modify: `README.md`
- Modify locally ignored: `summarizer.md`

- [ ] Document JWT settings and the current P1 scope.
- [ ] Run backend tests/lint, frontend lint/typecheck/build, Docker Compose config, and security gate.
- [ ] Commit and push as `Abhigyan6091 <abhigyan.sharma6091@gmail.com>`.
