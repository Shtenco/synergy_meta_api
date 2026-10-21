import asyncio
import httpx
from fastapi.testclient import TestClient
from synergy_meta_api.app import app
from synergy_meta_api.public_catalog import github_repository, mcp_registry_page

def test_real_protocol_github_mock():
    def handler(req):
        assert str(req.url) == "https://api.github.com/repos/modelcontextprotocol/registry"
        return httpx.Response(200, json={"full_name": "modelcontextprotocol/registry",
                                          "html_url": "https://github.com/modelcontextprotocol/registry",
                                          "default_branch": "main", "license": {"spdx_id": "MIT"}})
    async def work():
        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
            return await github_repository("modelcontextprotocol/registry", client=client)
    result = asyncio.run(work())
    assert result["executable"] is False
    assert result["name"] == "modelcontextprotocol/registry"

def test_official_mcp_protocol_mock():
    async def work():
        async with httpx.AsyncClient(transport=httpx.MockTransport(
            lambda request: httpx.Response(200, json={"servers": [{"server": {"name":"test"}}]}))) as client:
            return await mcp_registry_page(client=client)
    assert len(asyncio.run(work())["servers"]) == 1

def test_unknown_url_rejected():
    import pytest
    with pytest.raises(ValueError):
        asyncio.run(github_repository("https://internal.example/private"))

def test_live_routes_off_by_default(monkeypatch):
    monkeypatch.delenv("SYNERGY_ENABLE_PUBLIC_DISCOVERY", raising=False)
    c = TestClient(app)
    assert c.get("/v1/public-catalog/github/modelcontextprotocol/registry").status_code == 503
    assert c.get("/v1/public-catalog/mcp").status_code == 503
