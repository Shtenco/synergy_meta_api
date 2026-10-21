# Architecture and integration boundaries

**V0.1:** An ASGI service serves a transparent, local allowlisted tool registry, metadata list of external projects, and a limited MCP JSON-RPC endpoint. These are not production credentials or working external integrations.

**Planned:** Discovery workers ingest authenticated registries into a normalized catalog (tool name, namespace, vendor, signature, schema, auth method, license, source commit, trust level). A policy engine checks tenant, identity, scope and approved outbound hosts before an adapter can execute. Gateway selection will be validated on concrete workloads instead of stacking competing proxies. Keep metering separate from tool calls and record stable provenance.

## Threat boundaries

- Treat descriptions and tool outputs as untrusted data, not executable instructions.
- No arbitrary upstream URLs accepted from HTTP clients.
- Default deny external execution and irreversible actions.
- Fail closed for permissions; constrain I/O, time, quotas and size.
- Isolate secrets server-side and audit grants.
- Track provenance and license of every installed component.

## What is NOT done

No global API crawler, cross-project monorepo vendoring, live OAuth integrations, MCP session negotiation, SSE streaming, A2A execution, load testing, or independent security review.
