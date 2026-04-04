# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## About

`django-admin-extended` is a Django package (PyPI: `django-admin-extended`, version in `setup.py`) that enhances the Django admin UI/UX. It is not a standalone Django project — there is no `manage.py` or test runner configured in this repo.

## Building / Publishing

```bash
# Build distribution
python setup.py sdist bdist_wheel

# Install locally for development
pip install -e .
```

## Management Commands

```bash
# Show migration dependency graph for an app
python manage.py migration_graph <app_label>
```

## Architecture

The package lives entirely in `admin_extended/`. Key layers:

### Base classes (`admin_extended/base/`)
- **`ExtendedAdminModel`** — the main base class consumers subclass. Composes three mixins:
  - `ObjectToolModelAdminMixin` — adds `change_form_object_tools` / `change_list_object_tools` lists; custom actions appear as buttons on change-form or change-list pages. Decorated with `@object_tool` from `admin_extended/decorators.py`.
  - `UIUtilsMixin` — HTML helper methods (`get_html_img_tag`, `get_html_a_tag`, `get_html_text_color`, `format_json`).
  - `DispayLinkAdapter` — auto-converts FK fields in `list_display` into clickable admin links.
- **`CustomTableAdminPage`** — an `admin.ModelAdmin` subclass that replaces the changelist with a custom HTML table; override `get_table_data()` to return `TableData` instances.

### Utils (`admin_extended/utils.py`)
- **`DefaultModelAdmin`** — subclass of `ExtendedAdminModel` that auto-populates `list_display` (all non-text fields) and `list_filter` (fields with choices), and adds `select_related` for all FK fields.
- **`auto_register_model_admin()`** — registers all non-Django models with `DefaultModelAdmin`; call from `admin.py` with optional `ignore_models` list.

### Chart feature (`admin_extended/models/chart.py`, `admin_extended/admin/chart.py`)
- `TimeSeriesChart` model stores chart configuration (target model, aggregate function, time field, optional split/filter fields).
- `TimeSeriesChartAdmin` exposes `/admin/admin_extended/timeserieschart/<id>/chart/` (rendered page) and `/metrics/` (JSON API used by Chart.js on the frontend).

### Settings (`admin_extended/settings.py`)
Consumer projects configure via `ADMIN_EXTENDED` dict in their `settings.py`. Available keys:
- `MENU_APP_ORDER` — list of app labels to control sidebar order
- `MENU_MODEL_ORDER` — list of model names to control sidebar order
- `APP_ICON` — dict mapping app label → FontAwesome icon class
- `MODEL_ADMIN_TABBED_INLINE` (default `True`) — whether inlines render as tabs
- `RAW_ID_FIELDS_AS_DEFAULT` (default `False`) — auto-set raw_id / autocomplete fields

### Templates & Static
Templates override Django admin templates in `admin_extended/templates/admin/`. Static assets (CSS/JS) are in `admin_extended/static/admin_extended/`. FontAwesome Free 5.15.4 is bundled via the `fontawesomefree` package dependency.

### `ExtendedAdminModel` view/edit/add mode
The class differentiates three page types (`view`, `edit`, `add`) based on URL params. In `view` mode `has_change_permission` returns `False` (read-only). Fields prefixed with `display_` are hidden in edit/add modes automatically. `ext_read_only_fields` and `ext_write_only_fields` class attributes further control per-mode field visibility. `super_admin_only_fields` hides fields from non-superusers.
