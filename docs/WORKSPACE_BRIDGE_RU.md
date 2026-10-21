# SYNERGY META-API ↔ AI WORKSPACE — private loopback bridge V0.1

## Scope
Actual cross-repository HTTP adapter from the META-API integration branch to the local Workspace service `127.0.0.1:8129`. The web page `synergy.github.io` is **not** connected to the private backend, and should not request or store admin tokens.

**Access:** `SYNERGY_META_BRIDGE_TOKEN` (operator bearer token) and `SYNERGY_WORKSPACE_TOKEN` (independent local Workspace bearer token), configured in the private server environment. If absent, endpoints return 503. If operator token wrong, 401. The bridge never accepts destination URLs from the request.

**Endpoints (private service only):**
- `GET /v1/bridge/workspace/capabilities` — Workspace capability catalog, no upstream side effects;
- `POST /v1/bridge/workspace/run` — only `workspace.tasks.list` and `workspace.capital.summary`, max 10 steps, strict args, fail-closed.

**Forbidden:** any investment order, arbitrary tool call, Avito posting, payments, messages, mutation-capable capital allocation, arbitrary URL, shell, tool-discovery that directly invokes arbitrary tools.

## Flow
```
Private operator HTTP client
  -> META-API bridge operator bearer
  -> strict allowlist and request shape validation
  -> Workspace loopback bearer
  -> SQLite task registry / source-annotated financial summary
  -> receipt hash + provenance + no external effects
```

**Not yet production:** bridge token is a local-development credential, not OIDC/MFA/RBAC. The server has no tenant-scoped bearer policies, remote TLS/mTLS, durable job queue, bank attestations or broker approvals. Publish behind a private network only after security review; never set this router live on a public internet service.

## Tests
`pytest -q tests/test_workspace_bridge.py`

Test suite mocks upstream HTTP; no real bank/API/LLM/Avito/GitHub or investment orders.
