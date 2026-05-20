"""Object tools subsystem — custom action buttons on change form / list."""
from .decorator import ObjectToolSpec, object_tool

__all__ = ["ObjectToolMixin", "ObjectToolSpec", "object_tool"]


def __getattr__(name: str):
    if name == "ObjectToolMixin":
        from .mixin import ObjectToolMixin
        return ObjectToolMixin
    raise AttributeError(name)
