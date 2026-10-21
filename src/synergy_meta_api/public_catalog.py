"""Safe, opt-in public GitHub and MCP registry metadata discovery; not execution."""
from __future__ import annotations
import httpx
from typing import Any

GITHUB_REPOS = "https://api.github.com/repos/"
MCP_REGISTRY = "https://registry.modelcontextprotocol.io/v0.1/servers"

async def github_repository(repository: str, *, client: httpx.AsyncClient | None = None) -> dict[str, Any]:
    """Read only public metadata; cannot fetch arbitrary URLs."""
    import re
    if not re.fullmatch(r"[A-Za-z0-9_.-]{1,100}/[A-Za-z0-9_.-]{1,100}", repository):
        raise ValueError("Invalid owner/repository")
    url = GITHUB_REPOS + repository
    own = client is None
    if own:
        client = httpx.AsyncClient(timeout=8, follow_redirects=False, trust_env=False)
    try:
        r = await client.get(url, headers={"Accept": "application/vnd.github+json"})
        r.raise_for_status()
        if len(r.content) > 2_000_000:
            raise ValueError("Response too large")
        data = r.json()
        return {
            "name": data["full_name"], "url": data["html_url"],
            "default_branch": data.get("default_branch"),
            "license": (data.get("license") or {}).get("spdx_id", "UNKNOWN"),
            "archived": bool(data.get("archived")),
            "source": "github",
            "executable": False,
        }
    finally:
        if own:
            await client.aclose()

async def mcp_registry_page(*, client: httpx.AsyncClient | None = None) -> dict[str, Any]:
    own = client is None
    if own:
        client = httpx.AsyncClient(timeout=8, follow_redirects=False, trust_env=False)
    try:
        r = await client.get(MCP_REGISTRY, params={"limit": 20})
        r.raise_for_status()
        if len(r.content) > 2_000_000:
            raise ValueError("Response too large")
        data = r.json()
        if not isinstance(data, dict) or not isinstance(data.get("servers"), list):
            raise ValueError("Invalid registry document")
        return {"source": "official-mcp-registry", "servers": data["servers"], "executable": False}
    finally:
        if own:
            await client.aclose()
