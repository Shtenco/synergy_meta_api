"""Standalone router for normalized, read-only discovery capabilities."""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Any
from .distillation import ToolCatalog, normalize_openapi

router = APIRouter(prefix="/v1/discovery", tags=["Discovery"])
catalog = ToolCatalog()

class OpenAPIImport(BaseModel):
    namespace: str = Field(min_length=1, max_length=100)
    document: dict[str, Any]

@router.post("/openapi/preview")
def preview(spec: OpenAPIImport) -> dict[str, Any]:
    # Preview only. Never executes imported operations.
    try:
        tools = normalize_openapi(spec.document, spec.namespace)
    except ValueError as exc:
        raise HTTPException(422, str(exc))
    return {"count": len(tools), "tools": tools, "executable": False}

@router.post("/openapi/register")
def register(spec: OpenAPIImport) -> dict[str, Any]:
    try:
        tools = normalize_openapi(spec.document, spec.namespace)
    except ValueError as exc:
        raise HTTPException(422, str(exc))
    # An in-memory prototype registration; not persistent or tenant-isolated.
    return {"registered": catalog.add(spec.namespace, tools), "catalog_total": catalog.count(),
            "executable": False}

@router.get("/search")
def search(q: str = "", limit: int = 20) -> dict[str, Any]:
    try:
        data = catalog.search(q, limit)
    except ValueError as exc:
        raise HTTPException(422, str(exc))
    return {"count": len(data), "tools": data}
