"""Finite deterministic workflow execution for local built-in read-only tools."""
from __future__ import annotations
from typing import Any, Callable


class WorkflowError(Exception):
    pass


def run_workflow(steps: list[dict[str, Any]],
                 invoke: Callable[[str, dict[str, Any]], dict[str, Any]]) -> dict[str, Any]:
    if not isinstance(steps, list) or not 1 <= len(steps) <= 20:
        raise WorkflowError("Workflow must have 1 to 20 steps")
    completed: list[dict[str, Any]] = []
    for index, step in enumerate(steps):
        if not isinstance(step, dict) or not isinstance(step.get("tool"), str):
            raise WorkflowError(f"Invalid step {index}")
        # Never eval expressions or load dynamic code. Only the core's allowlisted tools run.
        args = step.get("arguments", {})
        if not isinstance(args, dict):
            raise WorkflowError(f"Invalid arguments at step {index}")
        try:
            output = invoke(step["tool"], args)
        except (ValueError, KeyError) as exc:
            return {"status": "failed", "failed_step": index, "error": str(exc),
                    "completed": completed}
        completed.append({"step": index, "tool": step["tool"], "result": output})
    return {"status": "succeeded", "completed": completed}
