"""Read-only, explicitly opt-in public registry discovery endpoints."""
import os
from fastapi import APIRouter, HTTPException
from .public_catalog import github_repository, mcp_registry_page

router = APIRouter(prefix="/v1/public-catalog", tags=["Public Catalog"])

def enabled():
    if os.environ.get("SYNERGY_ENABLE_PUBLIC_DISCOVERY") != "true":
        raise HTTPException(503, "Live discovery disabled by default")

@router.get("/github/{owner}/{repository}")
async def github_lookup(owner: str, repository: str):
    enabled()
    try:
        return await github_repository(f"{owner}/{repository}")
    except ValueError as exc:
        raise HTTPException(422, str(exc))
    except Exception as exc:
        raise HTTPException(502, "Public GitHub lookup failed") from exc

@router.get("/mcp")
async def mcp_lookup():
    enabled()
    try:
        return await mcp_registry_page()
    except Exception as exc:
        raise HTTPException(502, "Public MCP registry lookup failed") from exc
