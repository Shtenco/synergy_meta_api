"""Catalog discovery ingestion: local file / caller-supplied document only.

Remote crawling is intentionally separated from trust and execution.
"""
from __future__ import annotations
import json
from pathlib import Path
from typing import Any
from .distillation import ToolCatalog, normalize_openapi


def import_openapi_file(path: Path, catalog: ToolCatalog, namespace: str) -> int:
    if path.stat().st_size > 10_000_000:
        raise ValueError("OpenAPI input too large")
    document = json.loads(path.read_text(encoding="utf-8"))
    return catalog.add(namespace, normalize_openapi(document, namespace))


def mcp_tools_from_listing(result: dict[str, Any]) -> list[dict[str, Any]]:
    """Normalize tools/list replies into non-executable catalog entries."""
    tools = result.get("tools")
    if not isinstance(tools, list):
        raise ValueError("Expected tools list")
    if len(tools) > 5000:
        raise ValueError("Tool list too large")
    return [{"name": t["name"], "description": str(t.get("description", ""))[:512],
             "inputSchema": t.get("inputSchema", {"type": "object", "properties": {}})}
            for t in tools if isinstance(t, dict) and isinstance(t.get("name"), str)]


def classify_sources(source: dict[str, Any]) -> str:
    category = source.get("category", "unknown")
    return {
        "catalog": "discovery", "registry": "discovery", "framework": "adapter",
        "gateway": "gateway", "llm-gateway": "model-routing",
        "connectors": "connector", "automation": "workflow",
        "reference": "compatibility", "adapter": "adapter"
    }.get(category, "review-required")
