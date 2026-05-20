"""Autoregister subsystem."""
from .default_admin import DefaultModelAdmin
from .registry import auto_register

__all__ = ["DefaultModelAdmin", "auto_register"]
