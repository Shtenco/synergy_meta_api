"""Workspace bridge for private local deployments.

Authenticated, loopback-only upstream, read-only orchestration.
No arbitrary URLs, tools, shell commands, provider actions or investment orders.
"""
from __future__ import annotations
import hmac
import os
from typing import Any
import httpx
from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel, Field

router=APIRouter(prefix="/v1/bridge/workspace",tags=["Workspace Bridge"])
UPSTREAM="http://127.0.0.1:8129"
ALLOWED=frozenset({"workspace.tasks.list","workspace.capital.summary"})

class LocalWorkflow(BaseModel):
    steps: list[dict[str,Any]]=Field(min_length=1,max_length=10)

def require_operator(authorization: str | None)->str:
    public_token=os.environ.get("SYNERGY_META_BRIDGE_TOKEN","")
    workspace_token=os.environ.get("SYNERGY_WORKSPACE_TOKEN","")
    if not public_token or not workspace_token:
        raise HTTPException(503,"Workspace bridge not configured")
    if not authorization or not hmac.compare_digest(authorization,"Bearer "+public_token):
        raise HTTPException(401,"Operator authorization required")
    return workspace_token

async def _call_workspace(path:str,token:str,method:str="GET",payload:dict | None=None)->dict:
    # Every path is authored server-side. It must never depend on caller-provided URLs.
    if path not in ("/v1/orchestration/capabilities","/v1/orchestration/run"):
        raise HTTPException(403,"Unknown upstream endpoint")
    headers={"Authorization":"Bearer "+token,"Accept":"application/json"}
    try:
        async with httpx.AsyncClient(trust_env=False,follow_redirects=False,timeout=5.0) as client:
            response=await client.request(method,UPSTREAM+path,headers=headers,json=payload)
    except httpx.RequestError as exc:
        raise HTTPException(503,"Workspace local backend unavailable") from exc
    if response.status_code!=200 or len(response.content)>1_000_000:
        raise HTTPException(502,"Workspace response unavailable")
    if "application/json" not in response.headers.get("content-type",""):
        raise HTTPException(502,"Workspace returned non-JSON")
    try:out=response.json()
    except ValueError as exc:raise HTTPException(502,"Invalid Workspace response") from exc
    if not isinstance(out,dict):raise HTTPException(502,"Invalid Workspace response")
    return out

@router.get("/capabilities")
async def capabilities(authorization:str | None=Header(default=None))->dict:
    token=require_operator(authorization)
    result=await _call_workspace("/v1/orchestration/capabilities",token)
    return {"source":"SYNERGY_AI_WORKSPACE_LOCAL","meta_bridge_read_only":True,"upstream":result}

@router.post("/run")
async def run_workflow(payload:LocalWorkflow,authorization:str | None=Header(default=None))->dict:
    token=require_operator(authorization)
    for step in payload.steps:
        if not isinstance(step,dict) or set(step)!={"capability","arguments"}:
            raise HTTPException(422,"Explicit capability and arguments required")
        name=step["capability"]
        args=step["arguments"]
        if name not in ALLOWED or not isinstance(args,dict):
            raise HTTPException(403,"Capability denied by META bridge")
        if name=="workspace.tasks.list" and args:
            raise HTTPException(422,"No arguments accepted for tasks.list")
        if name=="workspace.capital.summary" and set(args)!={"currency","start","end"}:
            raise HTTPException(422,"Strict summary arguments required")
    result=await _call_workspace("/v1/orchestration/run",token,method="POST",payload={"steps":payload.steps})
    return {"source":"SYNERGY_META_API_BRIDGE","result":result,"external_provider_actions":False}
