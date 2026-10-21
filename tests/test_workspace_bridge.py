"""Loopback META / Workspace bridge never allows mutating providers or arbitrary calls."""
import pytest
from fastapi.testclient import TestClient
from synergy_meta_api.app import app
from synergy_meta_api import workspace_bridge_api as bridge

client=TestClient(app)
URL="/v1/bridge/workspace"

def test_not_configured_denies(monkeypatch):
 monkeypatch.delenv("SYNERGY_META_BRIDGE_TOKEN",raising=False)
 monkeypatch.delenv("SYNERGY_WORKSPACE_TOKEN",raising=False)
 assert client.get(URL+"/capabilities",headers={"Authorization":"Bearer anything"}).status_code==503

def test_missing_authorization_denies(monkeypatch):
 monkeypatch.setenv("SYNERGY_META_BRIDGE_TOKEN","operator-secret")
 monkeypatch.setenv("SYNERGY_WORKSPACE_TOKEN","workspace-secret")
 assert client.get(URL+"/capabilities").status_code==401
 assert client.get(URL+"/capabilities",headers={"Authorization":"Bearer other"}).status_code==401

def test_local_read_only_capabilities(monkeypatch):
 monkeypatch.setenv("SYNERGY_META_BRIDGE_TOKEN","operator-secret")
 monkeypatch.setenv("SYNERGY_WORKSPACE_TOKEN","workspace-secret")
 async def mocked(path,token,method="GET",payload=None):
  assert path=="/v1/orchestration/capabilities"
  assert token=="workspace-secret"
  return {"capabilities":[{"id":"workspace.capital.summary","effect":"read"}],"external_execution":False}
 monkeypatch.setattr(bridge,"_call_workspace",mocked)
 r=client.get(URL+"/capabilities",headers={"Authorization":"Bearer operator-secret"})
 assert r.status_code==200
 assert r.json()["meta_bridge_read_only"] is True

def test_unknown_mutations_denied_before_upstream(monkeypatch):
 monkeypatch.setenv("SYNERGY_META_BRIDGE_TOKEN","operator-secret")
 monkeypatch.setenv("SYNERGY_WORKSPACE_TOKEN","workspace-secret")
 async def fail(*args,**kwargs):raise AssertionError("should not call upstream")
 monkeypatch.setattr(bridge,"_call_workspace",fail)
 hdr={"Authorization":"Bearer operator-secret"}
 bad=[
  [{"capability":"external.avito.publish","arguments":{}}],
  [{"capability":"workspace.capital.allocate.plan","arguments":{}}],
  [{"capability":"shell.exec","arguments":{"cmd":"ls"}}],
  [{"capability":"workspace.capital.summary","arguments":{"currency":"KZT","start":"2026-10-01","end":"2026-10-31"}},{"capability":"external.investment.trade","arguments":{}}]
 ]
 for steps in bad:
  r=client.post(URL+"/run",json={"steps":steps},headers=hdr)
  assert r.status_code==403

def test_valid_workflow_calls_local_only(monkeypatch):
 monkeypatch.setenv("SYNERGY_META_BRIDGE_TOKEN","operator-secret")
 monkeypatch.setenv("SYNERGY_WORKSPACE_TOKEN","workspace-secret")
 async def fake(path,token,method="GET",payload=None):
  assert path=="/v1/orchestration/run"
  assert method=="POST"
  assert token=="workspace-secret"
  assert payload["steps"][0]["capability"]=="workspace.capital.summary"
  return {"status":"completed_local","external_effects":False,"receipt_sha256":"0"*64}
 monkeypatch.setattr(bridge,"_call_workspace",fake)
 r=client.post(URL+"/run",headers={"Authorization":"Bearer operator-secret"},json={
   "steps":[{"capability":"workspace.capital.summary","arguments":{"currency":"KZT","start":"2026-10-01","end":"2026-10-31"}}]})
 assert r.status_code==200
 assert r.json()["result"]["external_effects"] is False
