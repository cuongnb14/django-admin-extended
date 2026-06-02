# Changelog

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- `create_db` management command: creates the database for a configured
  connection if it does not exist. Supports PostgreSQL and MySQL, reads
  connection details from `settings.DATABASES`, accepts a `--database` alias
  (default: `default`), and is idempotent (skips creation when the database
  already exists).

## [6.0.1] — 2026-05-22

### Fixed

- `change_form`: Edit button in view-mode was gated on
  `has_change_permission or has_delete_permission`. Because
  `ExtendedModelAdmin.has_change_permission` returns `False` in VIEW mode, the
  condition collapsed to delete permission — hiding the Edit button from users
  with only change permission, and showing it to delete-only users. The button
  is now gated on a new `ae_has_change_permission` context variable that
  reflects the underlying model-level change permission.

### Changed

- `change_form`: Edit button is now rendered after user-defined object tools,
  so it sits at the end of the object-tools toolbar.

## [6.0.0] — 2026-05-20

### ⚠️ Breaking changes

v6 is a complete re-architecture. **No automatic upgrade path from v5.x.**
Use only for new installations or projects that accept manual migration.

- **Python 3.12+ required** (was 3.8+).
- **Django 5.2 LTS or Django 6.0+ required** (was 4.0).
- `bookmarks` and `charts` are now separate Django sub-apps; add
  `admin_extended.bookmarks` and `admin_extended.charts` to `INSTALLED_APPS`
  if you need them.
- Public API renames — see the rename table in
  `docs/superpowers/specs/2026-05-20-v6-architecture-refactor-design.md`.

### Removed

- `BookmarkAdmin.add_bookmark_view` (CSRF-disabled POST endpoint — security issue).
- `request.page_type` attribute (use `get_page_mode(request, object_id)` or `current_page_mode()`).
- `ExtendedModelAdmin.get_html_*` methods (use free functions `admin_extended.display.html_*`).
- `ExtendedModelAdmin.TEXT_COLOR_*` constants (use `admin_extended.display.html.{SUCCESS,ERROR,WARNING,DEFAULT}`).
- `setup.py`, `MANIFEST.in`.
- v5 packages `admin_extended.base`, `admin_extended.admin`, `admin_extended.models`,
  `admin_extended.utils`, `admin_extended.decorators`, `admin_extended.settings`.

### Fixed

- `TableData` shared mutable state via class-level lists (B1).
- `BookmarkAdmin.add_bookmark_view` CSRF disabled (B2).
- Mutable default arguments throughout the codebase (B3).
- `auto_register` reverse identity format — now canonical `app_label.ModelName` (B4).
- `DefaultModelAdmin` `JsonField` typo → `JSONField` (B5).
- `request.page_type` mutation — moved to `ContextVar` (B6).
- `DisplayLinkAdapter` skipped the first `list_display` entry (B7).
- `parse_filters` did not URL-decode (B8).
- `extra_context` mutation could overwrite caller-supplied keys (B9).
- `SCALE_MAPPING` duplicated between model and admin (B10).
- Sidebar templatetag ran a DB query per render (B11) — now cached with signal-based invalidation.
- `metrics_api` raised bare `Exception` (B12) — now returns proper 400 JSON.

### Added

- Type hints across the entire public API + `py.typed` marker.
- Permission check for object tool views (H2).
- `TimeSeriesChart.max_points` to cap returned buckets.
- `TimeSeriesChart.cache_seconds` for per-chart result caching.
- `TimeSeriesChart.clean()` validates target model and field references.
- `BOOKMARK_CACHE_SECONDS`, `DEFAULT_APP_ICON` settings.
- pytest + pytest-django + tox matrix (Python 3.12/3.13 × Django 5.2/6.0) + CI workflow.
- `pyproject.toml`, `ruff`, `mypy --strict`, `setuptools-scm` dynamic versioning.
