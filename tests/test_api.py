from fastapi.testclient import TestClient
from synergy_meta_api.app import app

client = TestClient(app)

def test_health():
    assert client.get("/healthz").json()["status"] == "ok"

def test_sources():
    body = client.get("/v1/sources").json()
    assert body["count"] == 18
    assert all(item["url"].startswith("https://github.com/") for item in body["sources"])

def test_tools():
    assert len(client.get("/v1/tools").json()["tools"]) == 2
    assert client.post("/v1/tools/call", json={"name": "synergy_health"}).json()["result"]["status"] == "ok"
    assert client.post("/v1/tools/call", json={"name": "unknown"}).status_code == 404

def test_mcp():
    def req(method, params=None):
        return client.post("/mcp", json={"jsonrpc": "2.0", "id": 1, "method": method, "params": params or {}}).json()
    assert req("initialize")["result"]["serverInfo"]["name"] == "synergy-meta-api"
    assert len(req("tools/list")["result"]["tools"]) == 2
    assert req("tools/call", {"name":"synergy_health"})["result"]["isError"] is False
    assert req("tools/call", {"name":"not-found"})["result"]["isError"] is True
    assert req("nonexistent")["error"]["code"] == -32601
