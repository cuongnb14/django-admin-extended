# CLAUDE.md

This file provides guidance to Claude Code when working with code in this repository.

## About

`django-admin-extended` (v6) is a Django package that enhances the Django admin UI/UX.

## Building / Testing

```bash
pip install -e ".[dev]"
pytest                  # full suite
tox                     # full matrix Python 3.12/3.13 x Django 5.2/6.0 + lint + type + build
python -m build         # build sdist + wheel
```

## INSTALLED_APPS

```python
INSTALLED_APPS = [
    'admin_extended',                  # required
    'admin_extended.bookmarks',        # optional sub-app
    'admin_extended.charts',           # optional sub-app
    # ...
]
```

## Architecture

- `admin_extended.conf.settings`: lazy proxy reading `settings.ADMIN_EXTENDED` per access (reactive to override_settings).
- `admin_extended.core`: `ExtendedModelAdmin`, `PageMode`, `get_page_mode`, fieldset filters, `delete_without_confirm` action.
- `admin_extended.display`: `DisplayLinkAdapter` (FK → link); free helpers `html_img`, `html_link`, `html_color`, `html_json`; color constants in `display.html`.
- `admin_extended.object_tools`: `@object_tool` decorator returns `ObjectToolSpec`; `ObjectToolMixin` dispatches with permission check.
- `admin_extended.autoregister`: `DefaultModelAdmin` + `auto_register(default_admin=..., ignore=['app_label.ModelName'])`.
- `admin_extended.custom_pages`: `CustomTableAdminPage` + `TableData` (dataclass with proper defaults).
- `admin_extended.bookmarks`: sub-app with `Bookmark` model + admin.
- `admin_extended.charts`: sub-app with `TimeSeriesChart` + `ChartQueryService` + class-based views.
- `admin_extended.templatetags`: `admin_extended_menu` (sort_apps, sort_models — cached bookmarks), `admin_extended_misc` (settings_value).
- `admin_extended.templates/admin/`: theme overrides for base_site, change_form, change_list, app_list.

## Page mode (view / edit / add)

Use `get_page_mode(request, object_id)` to detect the mode. The mode is also set in a `ContextVar` while `_changeform_view` runs — read it inside admin methods with `current_page_mode()`. The request is never mutated.
