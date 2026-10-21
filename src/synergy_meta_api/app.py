"""SYNERGY META-API V0.1: read-only registry plus limited MCP JSON-RPC transport."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel, Field

ROOT = Path(__file__).resolve().parents[2]
SOURCE_FILE = ROOT / "upstreams.json"
app = FastAPI(title="SYNERGY META-API", version="0.1.0")

class ToolCall(BaseModel):
    name: str
    arguments: dict[str, Any] = Field(default_factory=dict)

TOOLS = [
    {"name": "synergy_health", "description": "Return read-only gateway status.", "inputSchema": {"type": "object", "properties": {}, "additionalProperties": False}},
    {"name": "synergy_list_sources", "description": "List registered open-source upstream metadata (no remote invocation).", "inputSchema": {"type": "object", "properties": {}, "additionalProperties": False}},
]

def sources() -> list[dict[str, str]]:
    with SOURCE_FILE.open(encoding="utf-8") as fh:
        return json.load(fh)["sources"]

def invoke(name: str, arguments: dict[str, Any]) -> dict[str, Any]:
    if arguments:
        raise ValueError("This read-only tool takes no arguments")
    if name == "synergy_health":
        return {"status": "ok", "mode": "local-read-only", "version": "0.1.0"}
    if name == "synergy_list_sources":
        return {"sources": sources()}
    raise KeyError(name)

@app.get("/healthz")
def health() -> dict[str, str]:
    return {"status": "ok", "version": "0.1.0"}

@app.get("/v1/sources")
def list_sources() -> dict[str, Any]:
    data = sources()
    return {"count": len(data), "sources": data}

@app.get("/v1/tools")
def list_tools() -> dict[str, Any]:
    return {"tools": TOOLS}

@app.post("/v1/tools/call")
def call_tool(call: ToolCall) -> dict[str, Any]:
    try:
        return {"result": invoke(call.name, call.arguments)}
    except KeyError:
        raise HTTPException(404, "Unknown tool")
    except ValueError as exc:
        raise HTTPException(422, str(exc))

@app.post("/mcp")
async def mcp(request: Request) -> Any:
    # Deliberately limited MCP JSON-RPC handling. No sessions/notifications streaming yet.
    try:
        payload = await request.json()
    except Exception:
        raise HTTPException(400, "Invalid JSON")
    if not isinstance(payload, dict):
        raise HTTPException(400, "Expected JSON-RPC object")
    if payload.get("jsonrpc") != "2.0":
        return {"jsonrpc": "2.0", "id": payload.get("id"), "error": {"code": -32600, "message": "Invalid Request"}}
    method = payload.get("method")
    if method == "notifications/initialized":
        from fastapi import Response
        return Response(status_code=202)
    identifier = payload.get("id")
    if identifier is None:
        return {"jsonrpc": "2.0", "id": None, "error": {"code": -32600, "message": "Missing id"}}
    try:
        if method == "initialize":
            result = {"protocolVersion": "2025-03-26", "capabilities": {"tools": {"listChanged": False}}, "serverInfo": {"name": "synergy-meta-api", "version": "0.1.0"}}
        elif method == "ping":
            result = {}
        elif method == "tools/list":
            result = {"tools": TOOLS}
        elif method == "tools/call":
            params = payload.get("params", {})
            if not isinstance(params, dict):
                raise ValueError("params must be object")
            result = {"content": [{"type": "text", "text": json.dumps(invoke(params.get("name", ""), params.get("arguments", {})), ensure_ascii=False)}], "isError": False}
        else:
            return {"jsonrpc": "2.0", "id": identifier, "error": {"code": -32601, "message": "Method not found"}}
    except (KeyError, ValueError, TypeError) as exc:
        result = {"content": [{"type": "text", "text": str(exc)}], "isError": True}
    return {"jsonrpc": "2.0", "id": identifier, "result": result}


# Distilled API discovery extensions (metadata-only)
from .registry_api import router as discovery_router
app.include_router(discovery_router)
