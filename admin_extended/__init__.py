"""django-admin-extended — UI/UX enhancements for the Django admin."""
from __future__ import annotations

try:
    from ._version import version as __version__  # written by setuptools-scm
except ImportError:  # pragma: no cover
    __version__ = "0.0.0+unknown"

default_app_config = "admin_extended.apps.AdminExtendedConfig"

__all__ = ["__version__", "default_app_config"]
