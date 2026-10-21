"""Deny-by-default execution policy for any future external adapter."""
from dataclasses import dataclass
from enum import Enum


class Decision(str, Enum):
    DENY = "deny"
    ALLOW = "allow"
    APPROVAL_REQUIRED = "approval_required"


@dataclass(frozen=True)
class ToolPermission:
    tenant: str
    tool: str
    scopes: frozenset[str]
    read_only: bool = True
    allow: bool = False


def decide(permission: ToolPermission | None, *, tenant: str, tool: str,
           required_scopes: set[str], mutating: bool) -> Decision:
    if permission is None or not permission.allow:
        return Decision.DENY
    if permission.tenant != tenant or permission.tool != tool:
        return Decision.DENY
    if not required_scopes.issubset(permission.scopes):
        return Decision.DENY
    if mutating:
        return Decision.APPROVAL_REQUIRED if not permission.read_only else Decision.DENY
    return Decision.ALLOW
