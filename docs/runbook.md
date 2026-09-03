# Sentinel Aegis Production Runbook

Date: 2026-09-03

Operational procedures for deploy, rollback, backup, and incident triage. Each procedure
is written to be followed under pressure: preconditions first, verification last.

## Service overview

| Property | Value |
| --- | --- |
| Namespace | `sentinel-aegis` |
| Deployment | `sentinel-aegis-backend` |
| Health endpoint | `GET /health` |
| Metrics | `GET /metrics` (Prometheus) |
| Dashboards | Grafana → "Sentinel Aegis Security Overview" |
| Datastores | PostgreSQL (primary), Redis (rate limits), Qdrant (vectors) |

## Severity levels

| Level | Definition | Response |
| --- | --- | --- |
| SEV1 | Guardrails bypassed in production, tenant data crossed boundaries, or the API is down | Page immediately, start an incident channel |
| SEV2 | A security gate regressed, approvals are not recording, or error rate is elevated | Respond within the hour |
| SEV3 | Degraded telemetry, dashboard gaps, or a single non-critical finding | Next business day |

---

## Deploy

**Preconditions**

- CI is green on the commit, including the regression suite and security gate.
- The migration is backward compatible with the currently deployed release.
- You know the current revision for rollback: `kubectl -n sentinel-aegis get deploy sentinel-aegis-backend -o jsonpath='{.metadata.annotations.deployment\.kubernetes\.io/revision}'`

**Procedure**

```bash
# 1. Record the current image for rollback
kubectl -n sentinel-aegis get deploy sentinel-aegis-backend \
  -o jsonpath='{.spec.template.spec.containers[0].image}'

# 2. Roll out
kubectl -n sentinel-aegis set image deployment/sentinel-aegis-backend \
  backend=ghcr.io/example/sentinel-aegis-backend:<tag> \
  migrate=ghcr.io/example/sentinel-aegis-backend:<tag>

# 3. Watch it land (init container runs migrations first)
kubectl -n sentinel-aegis rollout status deployment/sentinel-aegis-backend --timeout=5m
```

**Verification**

```bash
curl -sI https://api.example.com/health | head -1
kubectl -n sentinel-aegis exec deploy/sentinel-aegis-backend -- \
  python -m app.cli.regression_suite
```

If the pod crash-loops on boot, read the logs first: the production preflight check prints
every unsafe setting it found. That is a configuration failure, not a code failure.

---

## Rollback

**When:** the regression suite fails against the new build, error rate rises, or a
security gate regressed after deploy.

```bash
# Fast path: undo the last rollout
kubectl -n sentinel-aegis rollout undo deployment/sentinel-aegis-backend
kubectl -n sentinel-aegis rollout status deployment/sentinel-aegis-backend --timeout=5m
```

**If the release included a migration**, rolling back the image is not enough — the schema
is still forward. Decide:

- **Backward-compatible migration (the normal case):** roll back the image only. The old
  code ignores the new columns. Leave the schema in place and remove it in a later release.
- **Breaking migration:** roll back the schema too, then the image:

```bash
kubectl -n sentinel-aegis scale deployment/sentinel-aegis-backend --replicas=0
kubectl -n sentinel-aegis run alembic-rollback --rm -it --restart=Never \
  --image=ghcr.io/example/sentinel-aegis-backend:<previous-tag> \
  --env="AEGIS_DATABASE_URL=$DATABASE_URL" \
  -- alembic downgrade <previous-revision>
kubectl -n sentinel-aegis rollout undo deployment/sentinel-aegis-backend
kubectl -n sentinel-aegis scale deployment/sentinel-aegis-backend --replicas=2
```

Never downgrade a migration that has already dropped a column holding data you still need.
Restore from backup instead.

---

## Backup and restore

**Schedule:** nightly `pg_dump` plus continuous WAL archiving. Monthly restore rehearsal.

Full commands are in `docs/deployment.md` §6. The short form:

```bash
# Back up
pg_dump --format=custom --compress=9 --dbname="$DATABASE_URL" --file="aegisai-$(date +%F).dump"
pg_restore --list "aegisai-$(date +%F).dump" > /dev/null   # verify readability

# Restore
kubectl -n sentinel-aegis scale deployment/sentinel-aegis-backend --replicas=0
pg_restore --dbname=aegisai_restored --clean --if-exists aegisai-<date>.dump
alembic current                                             # confirm revision
kubectl -n sentinel-aegis scale deployment/sentinel-aegis-backend --replicas=2
```

Backups contain attack payloads, findings, and redacted customer context. Encrypt them and
apply the same access controls as the live database.

---

## Incident triage

### 1. Guardrail bypass in production (SEV1)

A prompt injection, tool abuse, or data-extraction attack reached an unmitigated outcome.

```bash
# What fired, and what did the runtime decide?
curl -s -H "authorization: Bearer $TOKEN" \
  'https://api.example.com/api/v1/findings?status=open' | jq '.[0]'

# Correlate the request through every layer
curl -s -H "authorization: Bearer $TOKEN" \
  https://api.example.com/api/v1/observability/traces | jq '.[0].spans'
```

**Contain**

1. If a tool action caused impact, tighten the active policy so the tool requires approval
   or is denied — policies change without a code deploy:
   `POST /api/v1/policies` then activate the new version.
2. If a tenant is under active attack, revoke the offending credential at the IdP.

**Eradicate and verify**

1. Promote the finding to a regression case:
   `POST /api/v1/findings/{id}/regression-case`
2. Confirm it fails against the current build — that proves the case reproduces the bypass.
3. Improve the guardrail or policy until the case passes.
4. Commit the fixture. CI now fails if the bypass ever returns.
5. Move the finding to `fixed`, then `closed`, recording the remediation.

### 2. Cross-tenant data exposure (SEV1)

1. Capture the request id and tenant ids from the trace before anything else.
2. Scale to zero if exposure is ongoing. Availability is the lesser loss.
3. Identify the query path that omitted the tenant filter. Every persisted read is tenant
   scoped; a bypass means a new query path missed it.
4. Add a regression test that asserts the cross-tenant read returns 404 before fixing it.
5. Follow your breach-notification obligations; findings and traces are the evidence trail.

### 3. Security gate regression in CI (SEV2)

The gate found an attack the runtime used to mitigate.

```bash
cd backend
python -m app.cli.security_gate --report-path gate.md --campaign-report-path campaign.json
python -m app.cli.regression_suite
```

Read `gate.md` — it lists each finding with the responsible component and a regression
assertion. Do not lower the thresholds to make CI pass. If the finding is a genuine
accepted risk, record it on the finding as `accepted_risk` with a written justification.

### 4. Elevated error rate (SEV2)

```bash
kubectl -n sentinel-aegis logs deploy/sentinel-aegis-backend --tail=200 | grep unhandled_error
```

Every error response carries `error.request_id`, echoed in the `x-request-id` header. Use
it to find the matching log line and trace. Errors never contain internal details by
design, so the log is the source of truth.

### 5. Provider outage or latency spike (SEV3)

The provider layer has timeouts and retries. If a provider is down, set
`AEGIS_LLM_PROVIDER=local` to fall back to the deterministic provider and restart. The
support agent keeps working with degraded answer quality; all guardrails stay active.

---

## Post-incident

Within five business days of a SEV1 or SEV2:

1. Every finding from the incident is triaged, with remediation recorded.
2. Every confirmed bypass has a committed regression case that failed before the fix.
3. The timeline (detection, containment, eradication, recovery) is written up.
4. Detection gaps become new attack seeds in the catalogue.

The measure of a good outcome is not that the incident was resolved — it is that CI now
fails if it recurs.
