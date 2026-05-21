"""Enforce subsystem dependency rules.

Allowed imports (target -> sources that may import it):
  conf            <- core, display, charts, bookmarks, theme templatetags
  display         <- core, charts
  core            <- object_tools, autoregister, custom_pages, charts
  bookmarks       <- (sub-app, no upstream)
  charts          <- (sub-app, no upstream)

Forbidden:
  conf importing anything from admin_extended
  core importing autoregister / custom_pages / bookmarks / charts
  display importing core / object_tools / autoregister / custom_pages / bookmarks / charts
  bookmarks importing core / object_tools / autoregister / custom_pages / charts / display
"""
from __future__ import annotations

import ast
from pathlib import Path

FORBIDDEN: dict[str, tuple[str, ...]] = {
    "admin_extended/conf.py": (
        "admin_extended.core", "admin_extended.display", "admin_extended.object_tools",
        "admin_extended.autoregister", "admin_extended.custom_pages",
        "admin_extended.bookmarks", "admin_extended.charts",
    ),
    "admin_extended/core/": (
        # core composes ObjectToolMixin into ExtendedModelAdmin — that is allowed.
        "admin_extended.autoregister", "admin_extended.custom_pages",
        "admin_extended.bookmarks", "admin_extended.charts",
    ),
    "admin_extended/display/": (
        "admin_extended.core", "admin_extended.object_tools", "admin_extended.autoregister",
        "admin_extended.custom_pages", "admin_extended.bookmarks", "admin_extended.charts",
    ),
    "admin_extended/bookmarks/": (
        "admin_extended.core", "admin_extended.object_tools", "admin_extended.autoregister",
        "admin_extended.custom_pages", "admin_extended.charts", "admin_extended.display",
    ),
}


def _modules_imported_by(path: Path) -> set[str]:
    src = path.read_text()
    tree = ast.parse(src)
    out: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                out.add(alias.name)
        elif isinstance(node, ast.ImportFrom) and node.module:
            out.add(node.module)
    return out


def _python_files(target: str) -> list[Path]:
    p = Path(target)
    if p.is_file():
        return [p]
    return [f for f in p.rglob("*.py") if "tests" not in f.parts and "migrations" not in f.parts]


def test_no_forbidden_imports():
    violations: list[str] = []
    for target, forbidden in FORBIDDEN.items():
        for file_path in _python_files(target):
            imports = _modules_imported_by(file_path)
            for mod in imports:
                if any(mod == bad or mod.startswith(bad + ".") for bad in forbidden):
                    violations.append(f"{file_path} imports forbidden module {mod}")
    assert not violations, "\n".join(violations)
