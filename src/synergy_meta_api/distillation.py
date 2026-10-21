"""Native distillation core: normalize OpenAPI operations into discoverable tool descriptions.

It never performs remote actions, resolves untrusted $ref URLs, or handles user credentials.
"""
from __future__ import annotations
import hashlib
import json
import re
from typing import Any

MAX_OPERATIONS = 5000
METHODS = {"get", "post", "put", "patch", "delete", "head", "options"}
SAFE_NAME = re.compile(r"[^a-zA-Z0-9_]+")


def _slug(value: str) -> str:
    name = SAFE_NAME.sub("_", value).strip("_").lower()
    if not name:
        name = "operation"
    return name[:80]


def canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def digest(value: Any) -> str:
    return hashlib.sha256(canonical_json(value).encode()).hexdigest()


def normalize_openapi(document: dict[str, Any], namespace: str = "openapi") -> list[dict[str, Any]]:
    """Convert local OpenAPI 3 documents to tool metadata, with no network access.

    Security: external schema refs are NOT resolved. Tool registration is metadata-only.
    """
    if not isinstance(document, dict) or not (str(document.get("openapi", "")).startswith("3.")):
        raise ValueError("OpenAPI 3.x document required")
    paths = document.get("paths")
    if not isinstance(paths, dict):
        raise ValueError("OpenAPI paths object required")
    output: list[dict[str, Any]] = []
    namespace = _slug(namespace)
    used: set[str] = set()
    for path, path_item in sorted(paths.items()):
        if not isinstance(path, str) or not path.startswith("/") or not isinstance(path_item, dict):
            continue
        for method, operation in path_item.items():
            if method.lower() not in METHODS or not isinstance(operation, dict):
                continue
            if len(output) >= MAX_OPERATIONS:
                raise ValueError("Too many operations")
            base = _slug(str(operation.get("operationId") or f"{method}_{path}"))
            name = f"{namespace}_{base}"
            if name in used:
                name += "_" + digest({"path": path, "method": method})[:8]
            used.add(name)
            parameters = (path_item.get("parameters") or []) + (operation.get("parameters") or [])
            if not isinstance(parameters, list):
                parameters = []
            properties: dict[str, Any] = {}
            required: list[str] = []
            for param in parameters:
                if not isinstance(param, dict) or "$ref" in param:
                    continue
                param_name = param.get("name")
                if not isinstance(param_name, str) or not param_name:
                    continue
                schema = param.get("schema", {"type": "string"})
                properties[param_name] = schema if isinstance(schema, dict) else {"type": "string"}
                if param.get("required") and param_name not in required:
                    required.append(param_name)
            body = operation.get("requestBody")
            if isinstance(body, dict) and not "$ref" in body:
                media = body.get("content", {}).get("application/json", {})
                if isinstance(media, dict) and isinstance(media.get("schema"), dict):
                    properties["body"] = media["schema"]
                    if body.get("required"):
                        required.append("body")
            schema = {"type": "object", "properties": properties, "additionalProperties": False}
            if required:
                schema["required"] = required
            output.append({
                "name": name,
                "description": str(operation.get("summary") or operation.get("description") or f"{method.upper()} {path}")[:512],
                "inputSchema": schema,
                "annotations": {"readOnlyHint": method.lower() in ("get", "head", "options")},
                "_meta": {"method": method.upper(), "path": path, "source": namespace, "executable": False},
            })
    return output


class ToolCatalog:
    """In-memory deterministic capability index; descriptions are untrusted metadata."""
    def __init__(self) -> None:
        self._tools: dict[str, dict[str, Any]] = {}

    def add(self, source: str, tools: list[dict[str, Any]]) -> int:
        namespace = _slug(source)
        count = 0
        for tool in tools:
            if not isinstance(tool, dict) or not isinstance(tool.get("name"), str):
                continue
            original = tool["name"]
            name = _slug(original)
            key = f"{namespace}:{name}"
            normalized = {**tool, "name": key, "source": namespace,
                          "executable": False, "trust": "unverified"}
            self._tools[key] = normalized
            count += 1
        return count

    def search(self, query: str, limit: int = 20) -> list[dict[str, Any]]:
        if not 1 <= limit <= 100:
            raise ValueError("limit out of bounds")
        terms = set(re.findall(r"[a-z0-9_]+", query.lower())) if query else set()
        results = []
        for tool in self._tools.values():
            hay = (str(tool.get("name", "")) + " " + str(tool.get("description", ""))).lower()
            score = sum(1 for term in terms if term in hay)
            if not terms or score:
                results.append((score, tool["name"], tool))
        results.sort(key=lambda x: (-x[0], x[1]))
        return [v for _, _, v in results[:limit]]

    def count(self) -> int:
        return len(self._tools)
