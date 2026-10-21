import asyncio
import httpx
import pytest
from fastapi.testclient import TestClient
from synergy_meta_api.app import app
from synergy_meta_api.runtime import Connector, ConnectorRegistry, external_call
from synergy_meta_api.workflow import run_workflow

client = TestClient(app)

def test_workflow_end_to_end():
    r = client.post("/v1/execution/workflows/run", json={"steps": [
        {"tool": "synergy_health"}, {"tool": "synergy_list_sources"}]})
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "succeeded"
    assert len(body["completed"][1]["result"]["sources"]) == 18

def test_unknown_workflow_tool_denied():
    r = client.post("/v1/execution/workflows/run", json={"steps": [{"tool": "shell_exec"}]})
    assert r.json()["status"] == "failed"

def test_external_execution_off_by_default(monkeypatch):
    monkeypatch.delenv("SYNERGY_ENABLE_CONNECTOR_CALLS", raising=False)
    r = client.post("/v1/execution/connectors/call", json={
        "connector": "demo", "path": "/v1/test"})
    assert r.status_code == 503

def test_connector_not_configured():
    from synergy_meta_api.runtime import load_connectors
    assert load_connectors().describe() == []

def test_connector_policy_rejects_unknown_path(monkeypatch):
    registry = ConnectorRegistry([Connector("example","https://api.example.com", frozenset({"/safe"}))])
    with pytest.raises(ValueError):
        asyncio.run(external_call(registry, "example", "/private"))

def test_connector_rejects_mutation():
    registry = ConnectorRegistry([Connector("example","https://api.example.com",
        frozenset({"/safe"}), frozenset({"GET","POST"}))])
    with pytest.raises(ValueError):
        asyncio.run(external_call(registry, "example", "/safe", "POST"))

def test_connector_mocked_http(monkeypatch):
    import synergy_meta_api.runtime as runtime
    monkeypatch.setattr(runtime, "verify_destination", lambda _: None)
    def handler(req: httpx.Request):
        assert req.url.path == "/status"
        return httpx.Response(200, json={"ready": True})
    async def run():
        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as http:
            return await external_call(
                ConnectorRegistry([Connector("demo", "https://api.example.com",
                                             frozenset({"/status"}))]),
                "demo", "/status", client=http)
    assert asyncio.run(run())["body"]["ready"] is True
