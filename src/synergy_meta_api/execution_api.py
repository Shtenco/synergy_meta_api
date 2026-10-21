"""Execution API: local workflows and explicitly allowed operator-configured GET connectors."""
from __future__ import annotations
from typing import Any
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from .app import invoke
from .workflow import run_workflow, WorkflowError
from .runtime import load_connectors, external_call

router = APIRouter(prefix="/v1/execution", tags=["Execution"])

class WorkflowRequest(BaseModel):
    steps: list[dict[str, Any]] = Field(min_length=1, max_length=20)

class ConnectorCall(BaseModel):
    connector: str
    path: str
    method: str = "GET"

@router.post("/workflows/run")
def execute_workflow(payload: WorkflowRequest) -> dict[str, Any]:
    try:
        return run_workflow(payload.steps, invoke)
    except WorkflowError as exc:
        raise HTTPException(422, str(exc))

@router.get("/connectors")
def connectors() -> dict[str, Any]:
    try:
        return {"connectors": load_connectors().describe()}
    except (ValueError, KeyError, TypeError) as exc:
        raise HTTPException(500, "Invalid operator connector configuration") from exc

@router.post("/connectors/call")
async def call_connector(payload: ConnectorCall) -> dict[str, Any]:
    # Disabled unless explicitly enabled by operator; no authentication yet.
    # Even the read-only endpoint is gated until the platform has auth.
    import os
    if os.environ.get("SYNERGY_ENABLE_CONNECTOR_CALLS") != "true":
        raise HTTPException(503, "Connector execution disabled until authentication is deployed")
    # This flag is intended ONLY for private development use, never public networking.
    try:
        return await external_call(load_connectors(), payload.connector,
                                   payload.path, payload.method)
    except ValueError as exc:
        raise HTTPException(403, str(exc))
    except Exception as exc:
        raise HTTPException(502, "Connector request failed") from exc
