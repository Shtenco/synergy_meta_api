# SYNERGY META-API

Unified API/MCP discovery and secure tool execution gateway. **Status: V0.1 prototype, not production-ready.**

## Run

```bash
python -m pip install -e '.[test]'
uvicorn synergy_meta_api.app:app --host 127.0.0.1 --port 8000
pytest -q
```

Visit `/healthz`, `/v1/sources`, `/v1/tools`, `/docs`. MCP Streamable HTTP-compatible JSON-RPC subset is exposed at `POST /mcp`. This release implements MCP initialize, ping, tools/list, tools/call for **local read-only tools only**, plus safe tools/call errors. It does NOT implement full MCP streaming, sessions, OAuth, A2A, external execution, or production tenancy.

## External upstream sources

The `upstreams.json` manifest references 18 upstream GitHub repositories. The `scripts/clone_upstreams.py` script clones each separately into an ignored local directory with its own license and history. The core does **not** pretend all these projects are one compatible executable; gateways are alternatives, catalogs are discovery sources, and workflows require explicit adapters. Review upstream licenses and pin revisions before redistributing or deploying. Third-party code is **not** owned by this repository's author.

```bash
python scripts/clone_upstreams.py --list
python scripts/clone_upstreams.py --all --depth 1
# To clone a single reviewed dependency:
python scripts/clone_upstreams.py --name agentgateway
```

This is an explicit manual step; neither installation nor API requests execute clones. Keep untrusted external source code out of production runtime until it is reviewed.

## Security model

No arbitrary URL proxying or remote shell invocation. Only registered local read-only calls are dispatchable. Never place real API keys in Git or send them to catalog endpoints. The discovery catalog consists of metadata and **does not grant API access**. Before making the platform public, add authenticated tenants, authorization and scopes, signed/pinned upstream versions, audit logs, timeouts, quotas, rate limits, egress policy, and secret management.

## Architecture roadmap

1. V0.1 local typed tool registry and MCP subset, tests and upstream manifest.
2. Registry ingestion from official MCP Registry and OpenAPI directory with validation, license metadata and provenance.
3. Verified OpenAPI adapters with auth vault, explicit per-tenant consent and outbound allowlist.
4. MCP transports, agentgateway integration, A2A, approval workflow, observability and billing.

See `docs/ARCHITECTURE.md`.
