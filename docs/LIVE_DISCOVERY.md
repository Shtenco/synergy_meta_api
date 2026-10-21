# Read-only public integrations

Set `SYNERGY_ENABLE_PUBLIC_DISCOVERY=true` **only in a controlled deployment**, then GET:
- `/v1/public-catalog/github/modelcontextprotocol/registry`
- `/v1/public-catalog/mcp`

These use the public GitHub REST repository metadata API and official MCP Registry REST API respectively. Both are explicit fixed-origin HTTPS integrations, no runtime URL proxy. No authentication headers or access tokens are sent. Rate limits and external-service failures apply. For automated CI we use HTTP mocks to verify protocol contracts without relying on internet connectivity.

No real live call from the deployed SYNERGY server has been performed or verified; tests cover mocked responses only.
