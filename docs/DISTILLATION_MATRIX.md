# SYNERGY capability distillation matrix (2026-10-21)

This maps upstream *concepts* and feature domains to original SYNERGY abstractions. It is **not** a claim that source code or all upstream functionality was copied or reimplemented.

| Upstream | Feature category | SYNERGY boundary | State |
|---|---|---|---|
| agentic-community/mcp-gateway-registry | Tool inventory, policy metadata | ToolCatalog / policy | Metadata MVP |
| agentgateway/agentgateway | MCP/A2A/LLM proxy | Future gateway adapter | Not implemented |
| activepieces/activepieces | Connectors/workflows | Future workflow executor | Not implemented |
| modelcontextprotocol/registry | Registry ingestion | Discovery normalization | Normalization only |
| punkpeye/awesome-mcp-servers | Curated MCP discovery | Upstream manifest | Manifest only |
| APIs-guru/openapi-directory | OpenAPI specs | normalize_openapi | Local documents only |
| PrefectHQ/fastmcp | MCP server/OpenAPI bridge | normalize_openapi | Limited metadata bridge |
| microsoft/mcp-gateway | MCP scaling | Future gateway adapter | Not implemented |
| BerriAI/litellm | LLM routing | Future model route registry | Not implemented |
| Portkey-AI/gateway | Resilient LLM gateway | Future model routing | Not implemented |
| ComposioHQ/composio | Authenticated agent actions | Tool permissions | Policy skeleton |
| PipedreamHQ/pipedream | Workflow connectors | Future connector layer | Not implemented |
| n8n-io/n8n | Orchestrated workflows | Future workflows | Not implemented |
| Kong/kong | API gateway/security | Policy skeleton | No production proxy |
| TykTechnologies/tyk | Multiprotocol gateway | Future protocol bridge | Not implemented |
| public-apis/public-apis | REST directories | Upstream manifest | Manifest only |
| modelcontextprotocol/servers | Reference servers | Basic MCP compatibility | Partial only |
| dx-corp/mcp-openapi | OpenAPI to MCP | normalize_openapi | Metadata only |

## GitHub metadata review (2026-10-21)

GitHub repository license identifiers from its REST metadata: Apache-2.0 for agentic-community/mcp-gateway-registry, agentgateway/agentgateway, PrefectHQ/fastmcp, Kong/kong; MIT for punkpeye/awesome-mcp-servers, microsoft/mcp-gateway, Portkey-AI/gateway, ComposioHQ/composio, public-apis/public-apis, dx-corp/mcp-openapi; CC0-1.0 for APIs-guru/openapi-directory. Activepieces, official MCP Registry, LiteLLM, Pipedream, n8n, Tyk and MCP reference servers yielded NOASSERTION and require manual LICENSE review. GitHub metadata is not a complete legal audit.

## Remaining verification gates

- Inspect source roots, README/config/tests, cross-module interfaces and dependency licenses for all 18.
- Record immutable upstream commit SHAs and reproducible builds.
- Cross-check OpenAPI 3.0/3.1, $ref handling, all MCP transports and versions, pagination.
- Add explicit authorization before any network access or mutating workflows.
- Execute integration/security/load tests, then deploy behind authenticated gateway.
