from synergy_meta_api.distillation import normalize_openapi, ToolCatalog
from synergy_meta_api.discovery import mcp_tools_from_listing, classify_sources
from synergy_meta_api.policy import ToolPermission, decide, Decision
from fastapi.testclient import TestClient
from synergy_meta_api.app import app

SPEC = {"openapi":"3.1.0","info":{"title":"Example","version":"1"},
        "paths":{"/records/{id}":{"get":{"operationId":"GetRecord","parameters":[{"in":"path","name":"id","required":True,"schema":{"type":"integer"}}]},
                  "post":{"operationId":"UpdateRecord","requestBody":{"required":True,"content":{"application/json":{"schema":{"type":"object"}}}}}}}}

def test_normalize():
    tools = normalize_openapi(SPEC, "example")
    assert len(tools) == 2
    assert tools[0]["name"].startswith("example_")
    assert {t["_meta"]["method"] for t in tools} == {"GET", "POST"}
    assert next(t for t in tools if t["_meta"]["method"]=="GET")["inputSchema"]["required"] == ["id"]
    assert next(t for t in tools if t["_meta"]["method"]=="POST")["annotations"]["readOnlyHint"] is False
    assert all(t["_meta"]["executable"] is False for t in tools)

def test_catalog():
    c = ToolCatalog()
    assert c.add("example", normalize_openapi(SPEC)) == 2
    assert len(c.search("GetRecord")) == 1
    assert c.count() == 2

def test_policy_fail_closed():
    p = ToolPermission("a","tool",frozenset({"read"}),allow=True)
    assert decide(p,tenant="a",tool="tool",required_scopes={"read"},mutating=False) == Decision.ALLOW
    assert decide(p,tenant="b",tool="tool",required_scopes=set(),mutating=False) == Decision.DENY
    assert decide(p,tenant="a",tool="tool",required_scopes=set(),mutating=True) == Decision.DENY

def test_mcp_tool_import():
    assert mcp_tools_from_listing({"tools":[{"name":"ping"}]})[0]["name"] == "ping"
    assert classify_sources({"category":"registry"}) == "discovery"

def test_routes():
    c = TestClient(app)
    result = c.post("/v1/discovery/openapi/preview",json={"namespace":"test","document":SPEC})
    assert result.status_code == 200
    assert result.json()["count"] == 2
    result = c.post("/v1/discovery/openapi/register",json={"namespace":"test","document":SPEC})
    assert result.status_code == 200
    assert c.get("/v1/discovery/search?q=GetRecord").json()["count"] == 1
