"""Explicitly configured external HTTP connectors: no caller-supplied destination URL."""
from __future__ import annotations
import ipaddress
import json
import os
import socket
from dataclasses import dataclass
from typing import Any
from urllib.parse import urlsplit

import httpx


@dataclass(frozen=True)
class Connector:
    name: str
    base_url: str
    allowed_paths: frozenset[str]
    methods: frozenset[str] = frozenset({"GET"})
    token_env: str | None = None


def verify_destination(base_url: str) -> None:
    url = urlsplit(base_url)
    if url.scheme != "https" or not url.hostname or url.username or url.password or url.query or url.fragment:
        raise ValueError("HTTPS connector host required")
    if url.port not in (None, 443):
        raise ValueError("Nonstandard ports forbidden")
    host = url.hostname
    if host == "localhost" or host.endswith(".localhost") or host.endswith(".local"):
        raise ValueError("Local destinations forbidden")
    try:
        infos = socket.getaddrinfo(host, 443, type=socket.SOCK_STREAM)
    except socket.gaierror as exc:
        raise ValueError("Destination DNS resolution failed") from exc
    addresses = {ipaddress.ip_address(info[4][0]) for info in infos}
    if not addresses or not all(a.is_global for a in addresses):
        raise ValueError("Non-public destination address forbidden")


class ConnectorRegistry:
    def __init__(self, connectors: list[Connector]):
        self._connectors = {c.name: c for c in connectors}

    def get(self, name: str) -> Connector:
        try:
            return self._connectors[name]
        except KeyError as exc:
            raise ValueError("Connector not configured") from exc

    def describe(self) -> list[dict[str, Any]]:
        return [{"name": c.name, "methods": sorted(c.methods), "paths": sorted(c.allowed_paths),
                 "authenticated": bool(c.token_env)} for c in self._connectors.values()]


def load_connectors() -> ConnectorRegistry:
    """Operator-owned config, never controlled through public API; default empty."""
    config = os.environ.get("SYNERGY_CONNECTORS_JSON", "[]")
    raw = json.loads(config)
    if not isinstance(raw, list) or len(raw) > 100:
        raise ValueError("Invalid connector configuration")
    entries = []
    for c in raw:
        entries.append(Connector(
            name=c["name"], base_url=c["base_url"],
            allowed_paths=frozenset(c["allowed_paths"]),
            methods=frozenset(c.get("methods", ["GET"])),
            token_env=c.get("token_env"),
        ))
    return ConnectorRegistry(entries)


async def external_call(registry: ConnectorRegistry, name: str, path: str,
                        method: str = "GET", body: Any = None,
                        *, client: httpx.AsyncClient | None = None) -> dict[str, Any]:
    cfg = registry.get(name)
    method = method.upper()
    if path not in cfg.allowed_paths or method not in cfg.methods:
        raise ValueError("Path or method not allowed")
    if method != "GET":
        raise ValueError("Mutating external operations require approval workflow (not implemented)")
    verify_destination(cfg.base_url)
    headers = {"Accept": "application/json"}
    if cfg.token_env:
        value = os.environ.get(cfg.token_env)
        if not value:
            raise ValueError("Connector secret not configured")
        headers["Authorization"] = f"Bearer {value}"
    url = cfg.base_url.rstrip("/") + path
    kwargs = {"headers": headers, "timeout": httpx.Timeout(8.0), "follow_redirects": False}
    if client is not None:
        response = await client.request(method, url, **kwargs)
    else:
        async with httpx.AsyncClient(trust_env=False) as http:
            response = await http.request(method, url, **kwargs)
    response.raise_for_status()
    if len(response.content) > 2_000_000:
        raise ValueError("Connector response too large")
    return {"status_code": response.status_code, "body": response.json()}
