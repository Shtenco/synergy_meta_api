# Phase 2: API and workflow execution

This phase provides a real HTTP client adapter and a deterministic multi-step workflow executor. It does NOT provide live credentials or any configured production integration.

### Local workflow E2E
```bash
curl -fsS http://127.0.0.1:8000/v1/execution/workflows/run \\
  -H 'Content-Type: application/json' \\
  -d '{"steps":[{"tool":"synergy_health"},{"tool":"synergy_list_sources"}]}'
```

### Operator-configured connector

Set `SYNERGY_CONNECTORS_JSON` to a JSON array such as:

```json
[{"name":"provider","base_url":"https://api.example.com","allowed_paths":["/v1/status"],"methods":["GET"],"token_env":"PROVIDER_TOKEN"}]
```

Connector execution is **disabled by default**. To run it in a private test environment only, set `SYNERGY_ENABLE_CONNECTOR_CALLS=true`. Do not expose this flag behind a public endpoint until authentication, per-tenant permissions, DNS rebinding controls and rate limits are implemented. No user-configurable URL or shell command is executed.

### Validation

`pytest -q` includes local workflow E2E and HTTP calls against an in-memory mock transport. Real network E2E and GitHub Actions results are tracked separately. HTTP connector validates HTTPS/public DNS, denies redirects and non-GET methods; these controls are insufficient for an exposed production SSRF threat model.
