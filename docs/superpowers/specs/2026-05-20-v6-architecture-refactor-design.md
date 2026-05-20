# django-admin-extended v6 — Architecture Refactor Design Spec

**Date:** 2026-05-20
**Author:** Cuong Nguyen
**Status:** Approved — ready for implementation planning

## Overview

This document specifies a major refactor of the `django-admin-extended` package from v5.1.6 to v6.0.0. The refactor is a **cleanup + modernization** effort that preserves all current features but restructures the codebase into feature-bounded subsystems, fixes a set of known bugs and design smells, adds a proper testing and tooling baseline, and updates to modern Python and Django targets.

v6 is a **hard break**. No backward-compatibility shims, no upgrade path from v5.x. v6 is intended for fresh installations only. Consumers of v5.x continue using v5.x or migrate manually following the CHANGELOG.

## Goals

1. Separate the codebase into well-bounded subsystems so each feature is understandable and testable in isolation.
2. Fix bugs and remove design smells documented in the v5 codebase audit.
3. Modernize tooling: PEP 621 packaging, type hints, lint, static type-checking, automated tests, CI.
4. Drop legacy Python and Django support; target Python 3.12+ and Django 5.2 LTS + 6.0.
5. Establish a clean public API surface that consumers can rely on.

## Non-goals

- Adding new user-facing features beyond the existing v5 feature set.
- Providing automatic data migration from v5 to v6.
- Publishing to PyPI in this milestone (consumers install via git for now).
- Implementing a full plugin system. Subsystems are split into Django sub-apps, but there is no dynamic plugin loader.

## Target Versions

| Component | v5 | v6 |
|---|---|---|
| Python | 3.8+ | **3.12+** |
| Django | 4.0 | **5.2 LTS** and **6.0+** |

The CI matrix tests Python {3.12, 3.13} × Django {5.2, 6.0} (4 cells).

## Architecture — Approach

The refactor follows a **subsystem-oriented** layout. Each feature lives in its own sub-package with a clear public interface and no upward imports.

`bookmarks` and `charts` are promoted to Django sub-apps that consumers must explicitly add to `INSTALLED_APPS`. This allows opting out of features (no Bookmark or chart tables in the database if the user does not need them) and enforces clean dependency boundaries.

Other subsystems (`core`, `display`, `object_tools`, `autoregister`, `custom_pages`, `management`) remain Python sub-packages — importing them activates the feature without a separate `INSTALLED_APPS` entry. Theme assets (templates, static files, and templatetags) live at the `admin_extended/` root rather than in a `theme/` sub-package because Django only auto-discovers those locations at the app root.

## Module Layout

Django's template, static, and templatetags finders only scan `<app>/templates/`, `<app>/static/`, and `<app>/templatetags/` (the app root) for apps in `INSTALLED_APPS`. The layout below respects that: shared theme assets, templatetags, and templates used by core sub-packages live at the `admin_extended/` root. The `bookmarks` and `charts` sub-apps are real Django apps with their own `apps.py`, so they may host their own `templates/`, `static/`, and `migrations/` directories.

```
admin_extended/
  __init__.py                  # exports VERSION
  apps.py                      # AdminExtendedConfig
  conf.py                      # AdminExtendedSettings (lazy proxy)
  py.typed                     # PEP 561 marker

  templates/admin/             # auto-discovered by Django
    base_site.html             # theme override
    change_form.html           # theme override
    change_list.html           # theme override
    app_list.html              # theme override
    search_form.html           # theme override
    admin_extended/
      object_tools/            # templates used by object_tools subsystem
        change_form_object_tools.html
        change_form_submit_row.html
      custom_pages/
        custom_table_page.html

  static/admin_extended/       # auto-discovered by Django
    css/
    js/

  templatetags/                # auto-discovered by Django
    __init__.py
    admin_extended_menu.py     # sort_apps, sort_models
    admin_extended_misc.py     # settings_value, FontAwesome helper

  core/
    __init__.py                # re-exports ExtendedAdminModel, PageMode, get_page_mode
    page_mode.py               # PageMode enum + ContextVar
    field_visibility.py        # filter_fieldsets_by_mode/by_user helpers
    model_admin.py             # ExtendedAdminModel (composes mixins)
    actions.py                 # delete_without_confirm action factory

  object_tools/
    __init__.py                # re-exports object_tool, ObjectToolMixin
    decorator.py               # @object_tool — returns ObjectToolSpec dataclass
    mixin.py                   # ObjectToolMixin
    views.py                   # dispatch view extracted from mixin

  display/
    __init__.py                # re-exports DisplayLinkAdapter, html helpers
    link_adapter.py            # DisplayLinkAdapter (typo fixed)
    html.py                    # html_img, html_link, html_color, html_json
                               # plus SUCCESS/ERROR/WARNING/DEFAULT constants

  autoregister/
    __init__.py
    default_admin.py           # DefaultModelAdmin
    registry.py                # auto_register()

  custom_pages/
    __init__.py
    table_page.py              # CustomTableAdminPage + TableData

  bookmarks/                   # Django sub-app
    __init__.py
    apps.py                    # label='admin_extended_bookmarks'
    models.py
    admin.py                   # uses ModelForm flow, no @csrf_exempt
    forms.py
    migrations/
    templates/admin/admin_extended/bookmarks/

  charts/                      # Django sub-app
    __init__.py
    apps.py                    # label='admin_extended_charts'
    models.py                  # TimeSeriesChart + enums + _TRUNC_FOR_SCALE
    services.py                # ChartQueryService
    forms.py                   # ChartParamsForm
    admin.py
    views.py                   # MetricsView, ChartView
    urls.py
    migrations/
    templates/admin/admin_extended/charts/

  management/
    __init__.py
    commands/
      migration_graph.py

  tests/                       # excluded from wheel
    conftest.py
    example_project/
      settings.py
      urls.py
      sample_app/
    test_*.py
```

### Dependency rules

```
conf
  └─ (no internal deps)

core, display
  └──> conf

object_tools, autoregister, custom_pages
  └──> core, display

bookmarks  (sub-app)
  └──> conf
       (does NOT depend on core; uses plain admin.ModelAdmin)

charts  (sub-app)
  └──> core, display, conf
```

The root-level `templates/`, `static/`, and `templatetags/` directories are Django-discovery locations, not Python packages with import dependencies. The templatetag for the sidebar bookmark section uses `apps.is_installed('admin_extended.bookmarks')` and lazy `apps.get_model()` to avoid a hard import dependency on the `bookmarks` sub-app.

A single test (`test_imports.py`) walks the Python import graph of the subsystems and asserts no upward imports exist.

### Consumer `INSTALLED_APPS`

```python
INSTALLED_APPS = [
    'admin_extended',                  # core, theme, helpers (required)
    'admin_extended.bookmarks',        # optional
    'admin_extended.charts',           # optional
    # ...
]
```

## Public API

### `admin_extended.core`

```python
from admin_extended.core import ExtendedAdminModel, PageMode, get_page_mode

class MyAdmin(ExtendedAdminModel):
    view_only_fields: list[str] = ['display_summary']
    edit_only_fields: list[str] = ['internal_notes']
    superuser_only_fields: list[str] = ['secret_flag']

    tabbed_inlines: bool = True
    skip_delete_confirm: bool = False
    auto_raw_id_fields: bool = False
```

`PageMode` is a `StrEnum` with values `VIEW`, `EDIT`, `ADD`. `get_page_mode(request)` returns the current mode. Implementation uses `contextvars.ContextVar` set with a token at the start of `_changeform_view` and reset in a `finally` block. The request object is never mutated.

### `admin_extended.object_tools`

```python
from admin_extended.object_tools import object_tool, ObjectToolMixin

class MyAdmin(ExtendedAdminModel):
    change_form_tools = ['recompute']
    change_list_tools = ['export_csv']

    @object_tool(icon='fas fa-sync', label='Recompute', method='GET')
    def recompute(self, request, object_id):
        ...

    @object_tool(
        icon='fas fa-download',
        label='Export CSV',
        method='POST',
        post_param='reason',
        require_permission='view',   # 'change' (default), 'view', or None
    )
    def export_csv(self, request):
        ...
```

The decorator attaches a frozen `ObjectToolSpec` dataclass to the function:

```python
@dataclass(frozen=True, slots=True)
class ObjectToolSpec:
    name: str
    label: str
    icon: str | None
    method: Literal['GET', 'POST']
    post_param: str | None
    require_permission: Literal['change', 'view', None]
    func: Callable
```

### `admin_extended.display`

```python
from admin_extended.display import (
    DisplayLinkAdapter,
    html_img,
    html_link,
    html_color,
    html_json,
)
from admin_extended.display.html import SUCCESS, ERROR, WARNING, DEFAULT
```

All HTML helpers are free functions, not methods. Color constants are module-level.

### `admin_extended.autoregister`

```python
from admin_extended.autoregister import auto_register, DefaultModelAdmin

auto_register(
    default_admin=DefaultModelAdmin,
    ignore=['myapp.SecretModel', 'auth.Group'],   # canonical 'app_label.ModelName'
)
```

### `admin_extended.conf`

```python
from admin_extended.conf import settings as ae_settings

ae_settings.MENU_APP_ORDER         # list[str]
ae_settings.MENU_MODEL_ORDER       # list[str]
ae_settings.APP_ICON               # dict[str, str]
ae_settings.TABBED_INLINES         # bool
ae_settings.AUTO_RAW_ID_FIELDS     # bool
ae_settings.DEFAULT_APP_ICON       # str
ae_settings.BOOKMARK_CACHE_SECONDS # int
```

Implementation: `AdminExtendedSettings.__getattr__` reads `django.conf.settings.ADMIN_EXTENDED` on every access, so `override_settings` in tests works correctly. No external dependency.

### `admin_extended.custom_pages`

```python
from admin_extended.custom_pages import CustomTableAdminPage, TableData

@dataclass
class TableData:
    header: str
    titles: list[str] = field(default_factory=list)
    rows: list[list] = field(default_factory=list)

    def add_row(self, row: list) -> None: ...
```

### Rename Table (v5 → v6)

| v5 | v6 |
|---|---|
| `ExtendedAdminModel.ext_read_only_fields` | `view_only_fields` |
| `ExtendedAdminModel.ext_write_only_fields` | `edit_only_fields` |
| `ExtendedAdminModel.super_admin_only_fields` | `superuser_only_fields` |
| `ExtendedAdminModel.tab_inline` | `tabbed_inlines` |
| `ExtendedAdminModel.delete_without_confirm` | `skip_delete_confirm` |
| `ExtendedAdminModel.raw_id_fields_as_default` | `auto_raw_id_fields` |
| `ExtendedAdminModel.get_html_img_tag()` | `display.html_img()` |
| `ExtendedAdminModel.get_html_a_tag()` | `display.html_link()` |
| `ExtendedAdminModel.get_html_text_color()` | `display.html_color()` |
| `ExtendedAdminModel.format_json()` | `display.html_json()` |
| `ExtendedAdminModel.TEXT_COLOR_*` | `display.html.{SUCCESS,ERROR,WARNING,DEFAULT}` |
| `request.page_type` | `get_page_mode(request)` |
| `DispayLinkAdapter` (typo) | `DisplayLinkAdapter` |
| `ObjectToolModelAdminMixin` | `ObjectToolMixin` |
| `change_form_object_tools` | `change_form_tools` |
| `change_list_object_tools` | `change_list_tools` |
| `@object_tool(description=...)` | `@object_tool(label=...)` |
| `@object_tool(http_method=...)` | `@object_tool(method=...)` |
| `@object_tool(post_param_title=...)` | `@object_tool(post_param=...)` |
| `auto_register_model_admin()` | `auto_register()` |
| `ignore_models=['model.app']` | `ignore=['app.Model']` |
| `MODEL_ADMIN_TABBED_INLINE` setting | `TABBED_INLINES` |
| `RAW_ID_FIELDS_AS_DEFAULT` setting | `AUTO_RAW_ID_FIELDS` |
| `TimeSeriesChart.app_label` field | `target_app_label` |
| `TimeSeriesChart.model_name` field | `target_model_name` |

## Bug Fixes and Semantic Changes

### Bugs

**B1. `TableData` shared mutable state.**
v5 declared `table_titles = []` and `table_rows = []` as class attributes, so every instance shared the same lists. v6 uses `field(default_factory=list)`. The method `add_rows(row)` is renamed to `add_row(row)` because its parameter is a single row, not a list of rows.

**B2. `BookmarkAdmin.add_bookmark_view` CSRF disabled.**
v5 exposed a `@csrf_exempt` POST endpoint that created `Bookmark` rows without origin checks. v6 removes the endpoint. Bookmark creation goes through the standard admin changeform with CSRF protection and permission checks.

**B3. Mutable default arguments.**
v5 had several mutable defaults (`ignore_models=[]`, class-level `change_form_object_tools = []`, etc). v6 uses `None` sentinel with internal default, or `field(default_factory=list)` for dataclasses.

**B4. `auto_register` reverse identity format.**
v5 used `f'{model._meta.model_name}.{model._meta.app_label}'` (reversed). v6 uses the canonical `'app_label.ModelName'` matching `django.apps.apps.get_model`.

**B5. `DefaultModelAdmin` `JsonField` typo.**
v5 had `list_display_ignore_field_type = ['TextField', 'JsonField']` — `JsonField` does not exist. v6 uses `['TextField', 'JSONField']` and compares via `isinstance(field, (TextField, JSONField))` to support subclasses.

**B6. `request.page_type` mutation.**
v5 assigned `request.page_type = ...` in `_changeform_view`. v6 uses `contextvars.ContextVar[PageMode]` set with a token and reset in `try/finally`. The request is never mutated.

**B7. `DisplayLinkAdapter.convert_display_fields` skips first element.**
v5 assumed `list_display[0]` was always `__str__` and skipped it. v6 processes the entire list. Skip conditions for FK linking are explicit: skip if the field is already in `list_display_links`, if the entry is a callable, or if the admin defines a method named `<field>_link`.

**B8. `parse_filters` does not URL-decode.**
v5 used naive `item.split('=')`. v6 uses `urllib.parse.parse_qsl(self.filters, keep_blank_values=False)`.

**B9. `extra_context` mutation can overwrite caller keys.**
v5 wrote `extra_context['change_form_object_tools']` directly. v6 namespaces all keys under `admin_extended_*` and templates reference the namespaced keys.

**B10. `SCALE_MAPPING` duplicated between `models/chart.py` and `admin/chart.py`.**
v6 puts the single source of truth in `charts/models.py` as `_TRUNC_FOR_SCALE` with a `trunc_for(scale)` helper.

**B11. Sidebar templatetag queries DB on every render and mutates input.**
v5 ran `Bookmark.objects.filter(...)` for every sidebar render and called `apps.sort(...)` (in-place). v6 caches the bookmark query for `BOOKMARK_CACHE_SECONDS` (default 60s) via `django.core.cache`. Cache invalidation uses `post_save` and `post_delete` signals on `Bookmark`. The templatetag returns a new list instead of sorting in place.

**B12. `metrics_api` raises bare `Exception`.**
v6 returns `JsonResponse({'errors': form.errors}, status=400)` and routes through `ChartQueryService`.

### Hardening

**H1. Type hints on the entire public API**, with a `py.typed` marker shipped in the wheel.

**H2. Permission check for object tool views.** Every object tool dispatch verifies the appropriate permission before invoking the tool function. The default is `'change'` permission. The decorator accepts `require_permission='change' | 'view' | None`.

**H3. URL name convention.** All custom URLs use the prefix `admin_extended_<subapp>_<action>` (Django admin does not support URL namespaces inside the admin site).

**H4. Cache `get_change_form_object_tools` per request.** Compute once in `changeform_view`, pass the result to render helpers.

**H5. Theme templatetag tolerates missing sub-apps.** `admin_extended_menu.py` checks `apps.is_installed('admin_extended.bookmarks')` and lazily resolves the model via `apps.get_model` inside a try/except. The bookmark sidebar section is hidden when the sub-app is not installed.

### Removed Features

| v5 | Reason |
|---|---|
| `BookmarkAdmin.add_bookmark_view` | Security (B2) |
| `request.page_type` attribute | Replaced by `get_page_mode(request)` (B6) |
| `ExtendedAdminModel.get_html_*` methods | Moved to free functions in `display.html` |
| `ExtendedAdminModel.TEXT_COLOR_*` constants | Moved to module-level in `display.html` |
| `setup.py` | Replaced by `pyproject.toml` |
| `MANIFEST.in` | Replaced by `pyproject.toml` `package-data` |

## Charts Subsystem Redesign

The charts subsystem is the most complex piece of v5 (~280 LOC mixing model, query, form validation, and view shaping). v6 splits responsibilities cleanly.

### Model changes

```python
class TimeSeriesChart(models.Model):
    name: str
    description: str | None
    chart_type: ChartType         # StrEnum
    stacked: bool

    default_time_range: TimeRange
    default_scale: Scale

    target_app_label: str          # was app_label
    target_model_name: str         # was model_name
    time_field: str
    aggregate: Aggregate
    aggregate_field: str = '*'
    aggregate_label: str
    split_field: str | None
    filter_field: str | None
    filters: str | None

    max_points: int = 1000         # NEW — cap on number of buckets
    cache_seconds: int = 0         # NEW — 0 = no cache; per-chart cache

    def clean(self):
        # Validates: target model exists, time_field/aggregate_field/split_field/filter_field
        # exist on the target model, aggregate_field is non-'*' for non-COUNT aggregates,
        # and filters parses cleanly with parse_qsl.
        ...
```

`Scale` enum holds the trunc mapping in the same module as the only source of truth:

```python
_TRUNC_FOR_SCALE = {
    Scale.HOUR: TruncHour,
    Scale.DAY: TruncDay,
    Scale.WEEK: TruncWeek,
    Scale.MONTH: TruncMonth,
}

def trunc_for(scale: Scale): ...
```

### Service layer

```python
@dataclass(frozen=True, slots=True)
class ChartParams:
    time_range: TimeRange
    scale: Scale
    filter_value: str | None = None

@dataclass(frozen=True, slots=True)
class ChartSeries:
    label: str
    data: list[float]

@dataclass(frozen=True, slots=True)
class ChartResult:
    chart_type: ChartType
    stacked: bool
    labels: list[str]
    datasets: list[ChartSeries]


class ChartQueryService:
    def __init__(self, chart: TimeSeriesChart): ...
    def filter_choices(self) -> list[tuple[str, str]]: ...     # cached 5min
    def run(self, params: ChartParams) -> ChartResult: ...
    def run_cached(self, params: ChartParams) -> ChartResult: ...  # uses chart.cache_seconds
```

The service is pure: it takes `ChartParams`, returns `ChartResult`. It never touches HTTP request/response objects. It is the only place that imports `TruncHour`/`TruncDay`/etc.

### Form

A single `ChartParamsForm` replaces v5's two forms. The `filter_value` field is added dynamically in `__init__` when `chart.filter_field` is set; otherwise it is removed from the form. `TypedChoiceField` is used for `time_range` so the cleaned value is `int`, not `str`.

### Views

Class-based views in `charts/views.py`:

- `MetricsView` returns JSON (status 200 with `ChartResult` shape, or 400 with form errors).
- `ChartView` renders the HTML wrapper with the form; the page's JS calls `MetricsView` to populate the chart.
- Both views check `request.user.is_staff` in `dispatch`.

### Admin

`TimeSeriesChartAdmin` becomes a thin layer that registers the URLs and adds a `chart_link` display column that uses `reverse()` instead of a hard-coded URL.

## Tooling and Build

### `pyproject.toml`

PEP 621 metadata. Version is dynamic via `setuptools-scm` (reads from git tag). The current placeholder version file `admin_extended/_version.py` is generated by the build, not checked in.

```toml
[build-system]
requires = ["setuptools>=68", "setuptools-scm>=8"]
build-backend = "setuptools.build_meta"

[project]
name = "django-admin-extended"
dynamic = ["version"]
requires-python = ">=3.12"
dependencies = [
    "Django>=5.2,<7.0",
    "fontawesomefree==5.15.4",
]

[project.optional-dependencies]
test = ["pytest>=8", "pytest-django>=4.8", "pytest-cov>=5"]
dev = [
    "django-admin-extended[test]",
    "ruff>=0.6",
    "mypy>=1.11",
    "django-stubs[compatible-mypy]>=5.1",
    "tox>=4",
    "build>=1.2",
]

[tool.setuptools.packages.find]
include = ["admin_extended*"]
exclude = ["admin_extended.tests*"]

[tool.setuptools.package-data]
"admin_extended" = ["py.typed", "templates/**/*", "static/**/*"]
"admin_extended.bookmarks" = ["templates/**/*"]
"admin_extended.charts" = ["templates/**/*"]

[tool.setuptools_scm]
write_to = "admin_extended/_version.py"

[tool.ruff]
line-length = 120
target-version = "py312"

[tool.ruff.lint]
select = ["E", "F", "I", "UP", "B", "DJ", "RUF", "SIM"]

[tool.mypy]
python_version = "3.12"
strict = true
plugins = ["mypy_django_plugin.main"]
exclude = ["admin_extended/tests/.*", "admin_extended/.*/migrations/.*"]

[tool.pytest.ini_options]
DJANGO_SETTINGS_MODULE = "admin_extended.tests.example_project.settings"
addopts = "-ra --strict-markers --cov=admin_extended --cov-report=term-missing"
```

### `tox.ini`

```ini
[tox]
envlist =
    py{312,313}-dj52
    py{312,313}-dj60
    lint
    type
    build
isolated_build = true

[testenv]
extras = test
commands = pytest {posargs}

[testenv:py312-dj52]
deps = Django>=5.2,<5.3
[testenv:py313-dj52]
deps = Django>=5.2,<5.3
[testenv:py312-dj60]
deps = Django>=6.0,<6.1
[testenv:py313-dj60]
deps = Django>=6.0,<6.1

[testenv:lint]
deps = ruff>=0.6
commands =
    ruff check admin_extended
    ruff format --check admin_extended

[testenv:type]
extras = dev
commands = mypy admin_extended

[testenv:build]
deps = build>=1.2
commands = python -m build --sdist --wheel
```

### CI

`.github/workflows/ci.yml`:

```yaml
name: CI
on:
  push:
    branches: [main]
  pull_request:

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      fail-fast: false
      matrix:
        python: ["3.12", "3.13"]
        django: ["52", "60"]
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.python }}
      - run: pip install tox
      - run: tox -e py${{ matrix.python }}-dj${{ matrix.django }}

  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: "3.12" }
      - run: pip install tox
      - run: tox -e lint

  type:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: "3.12" }
      - run: pip install tox
      - run: tox -e type

  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: "3.12" }
      - run: pip install tox
      - run: tox -e build
      - uses: actions/upload-artifact@v4
        with:
          name: dist
          path: dist/
```

No release workflow in v6.0.0. Consumers install via:

```bash
pip install "git+https://github.com/cuongnb14/django-admin-extended.git@v6.0.0"
```

Publishing to PyPI is deferred to a future minor release.

### Repo file changes

| File | v5 | v6 |
|---|---|---|
| `setup.py` | present | deleted |
| `MANIFEST.in` | present | deleted |
| `README.rst` | RST | renamed `README.md` (Markdown) |
| `pyproject.toml` | absent | added |
| `tox.ini` | absent | added |
| `.pre-commit-config.yaml` | absent | added (optional for contributors) |
| `.github/workflows/ci.yml` | absent | added |
| `CHANGELOG.md` | absent | added (Keep a Changelog format) |
| `CONTRIBUTING.md` | absent | added |
| `CLAUDE.md` | present | updated to reflect new structure |
| `llms.txt` | present | updated to reflect new API |
| `.gitignore` | present | adds `_version.py`, `dist/`, `*.egg-info/` |

## Testing Strategy

A `pytest` + `pytest-django` suite lives under `admin_extended/tests/` and is excluded from the wheel.

### Test layout

```
admin_extended/tests/
  conftest.py                  # DB fixture, user/superuser/admin client
  example_project/
    settings.py                # minimal Django settings, includes ADMIN_EXTENDED
    urls.py
    sample_app/
      models.py                # Order, Customer (FK), Product
      admin.py
      migrations/
  test_conf.py
  test_core_model_admin.py
  test_core_page_mode.py
  test_object_tools.py
  test_display_link.py
  test_display_html.py
  test_autoregister.py
  test_bookmarks.py
  test_charts_models.py
  test_charts_service.py
  test_charts_views.py
  test_custom_pages.py
  test_management_commands.py
  test_imports.py              # asserts dependency rule graph
```

### Coverage targets

- 85% line coverage overall.
- 100% line coverage for `core/`, `display/link_adapter.py`, `object_tools/`, `charts/services.py`.

### Notable regression tests

- `test_custom_pages.py` creates two `TableData` instances and asserts that adding a row to one does not affect the other (B1).
- `test_core_page_mode.py` runs two parallel-style requests via threading + `ContextVar` and asserts the modes do not leak.
- `test_display_link.py` asserts FK linking when `list_display` does not contain `__str__` as the first element (B7).
- `test_charts_service.py` builds 30 rows of sample data and asserts label and series shape for each combination of scale and aggregate.

## Implementation Order

The refactor is structured into 13 steps. Steps 2 through 9 are largely independent and can be parallelized; step 10 depends on 2, 3, and 5; step 11 depends on 9.

1. **Foundation:** `pyproject.toml`, delete `setup.py`/`MANIFEST.in`, `tox.ini`, CI workflow, `tests/example_project` skeleton, `conftest.py`. Result: `pytest` runs with zero tests passing.
2. **`conf.py`:** lazy settings proxy with full test coverage (including `override_settings`).
3. **`core/page_mode.py` + `core/field_visibility.py`:** pure logic, unit-tested first.
4. **`display/` (link_adapter + html):** extract from mixin, test idempotency and the B7 regression case.
5. **`core/model_admin.py` `ExtendedAdminModel`:** compose page_mode + display + field_visibility. Integration tests with `sample_app`.
6. **`object_tools/`:** dataclass spec + decorator + mixin + dispatch view + permission check (H2). Tests cover the full request lifecycle.
7. **`autoregister/`:** corrected ignore format + test with `sample_app`.
8. **`custom_pages/`:** `TableData` fix + regression test (B1).
9. **`bookmarks/` sub-app:** model + admin without `@csrf_exempt` + templatetag sidebar section + tests.
10. **`charts/` sub-app:** model with `clean()` + `ChartQueryService` + `ChartParamsForm` + class-based views + admin + cache + tests.
11. **Theme assets:** root-level `templatetags/admin_extended_menu.py` + `admin_extended_misc.py`, template overrides under `templates/admin/`, static under `static/admin_extended/`. Manual smoke test in `example_project` (`runserver`).
12. **`management/commands/migration_graph.py`:** type hints + tests.
13. **Documentation + `CHANGELOG.md` + git tag `v6.0.0`.**

Each step is a natural commit/PR boundary.

## Risks and Mitigations

| Risk | Mitigation |
|---|---|
| Django 6.0 breaks the codebase | CI matrix catches early; fix in the same refactor step. |
| `mypy strict` creates excessive friction | Allow `# type: ignore[code]` with a comment explaining each instance; refine over time. |
| Performance regression from chart cache layer | Test with a 10K-row fixture; `cache_seconds=0` default means no behavior change. |
| Subsystem split prevents v5 users from upgrading | Accepted by design: v6 is fresh-install only. Documented in README and CHANGELOG. |
| Sidebar templatetag fails when `bookmarks` is not installed | Lazy import + `apps.is_installed` guard (H5). |
| Import-cycle introduced accidentally during refactor | `test_imports.py` enforces the dependency rule graph. |

## CHANGELOG entry

```markdown
## [6.0.0] — 2026-XX-XX

### ⚠️ Breaking changes

v6 is a complete re-architecture. **No automatic upgrade path from v5.x.**
Use only for new installations or projects that accept manual migration.

- **Python 3.12+ required** (was 3.8+)
- **Django 5.2 LTS or Django 6.0+ required** (was 4.0)
- `bookmarks` and `charts` are now separate Django sub-apps; add
  `admin_extended.bookmarks` and `admin_extended.charts` to `INSTALLED_APPS`
  if you need them.
- Many public API renames — see the migration table in
  docs/superpowers/specs/2026-05-20-v6-architecture-refactor-design.md.

### Removed
- `BookmarkAdmin.add_bookmark_view` (CSRF-disabled POST endpoint, security issue)
- `request.page_type` attribute (use `get_page_mode(request)`)
- `ExtendedAdminModel.get_html_*` methods (use `admin_extended.display.html_*`)
- `ExtendedAdminModel.TEXT_COLOR_*` constants
  (use `admin_extended.display.html.{SUCCESS,ERROR,WARNING,DEFAULT}`)
- `setup.py`, `MANIFEST.in`

### Fixed
- TableData shared mutable state (B1)
- BookmarkAdmin CSRF disabled (B2)
- Mutable default arguments throughout (B3)
- auto_register reverse identity format (B4)
- DefaultModelAdmin `JsonField` typo (B5)
- request.page_type mutation (B6)
- DisplayLinkAdapter skipped first list_display element (B7)
- parse_filters did not URL-decode (B8)
- extra_context mutation overwriting caller keys (B9)
- SCALE_MAPPING duplication (B10)
- Sidebar templatetag DB query per render (B11)
- metrics_api bare Exception (B12)

### Added
- Type hints throughout the public API + `py.typed` marker
- Permission checks for object tool views (H2)
- `TimeSeriesChart.max_points` query cap
- `TimeSeriesChart.cache_seconds` per-chart cache
- `TimeSeriesChart.clean()` validation
- `BOOKMARK_CACHE_SECONDS`, `DEFAULT_APP_ICON` settings
- Test suite + tox matrix + CI workflow
- `pyproject.toml`, `ruff`, `mypy --strict`
```
