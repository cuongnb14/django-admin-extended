"""@object_tool decorator and ObjectToolSpec dataclass."""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any, Literal

Method = Literal["GET", "POST"]
RequirePermission = Literal["change", "view"] | None


@dataclass(frozen=True, slots=True)
class ObjectToolSpec:
    name: str
    label: str
    icon: str | None
    method: Method
    post_param: str | None
    require_permission: RequirePermission
    func: Callable[..., Any]


def object_tool(
    *,
    label: str,
    icon: str | None = None,
    method: Method = "GET",
    post_param: str | None = None,
    require_permission: RequirePermission = "change",
    name: str | None = None,
) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """Mark a ModelAdmin method as an object tool."""
    if method not in ("GET", "POST"):
        raise ValueError(f"object_tool method must be 'GET' or 'POST', got {method!r}")
    if require_permission not in ("change", "view", None):
        raise ValueError(
            f"object_tool require_permission must be 'change', 'view', or None, got {require_permission!r}"
        )

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        spec = ObjectToolSpec(
            name=name or func.__name__,
            label=label,
            icon=icon,
            method=method,
            post_param=post_param,
            require_permission=require_permission,
            func=func,
        )
        func.object_tool = spec  # type: ignore[attr-defined]
        return func

    return decorator
