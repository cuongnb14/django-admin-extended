# django-admin-extended

A Django package that enhances the Django admin UI/UX with charts, bookmarks, custom views, and improved model admin features.

Targets: Django 5.2 / 6.0 on Python 3.12 / 3.13.

## Installation

```python
# settings.py
INSTALLED_APPS = [
    'admin_extended',                  # required
    'admin_extended.bookmarks',        # optional — bookmark sidebar feature
    'admin_extended.charts',           # optional — time series chart feature
    'fontawesomefree',                 # required — bundles FontAwesome 5 static files
    # ... other Django apps (admin, auth, contenttypes, sessions, messages, staticfiles)
]
```

`admin_extended.bookmarks` and `admin_extended.charts` are independent sub-apps with their own migrations. Only add them if you need those features.

No URL configuration needed. The package overrides Django admin templates automatically.

## Settings

Configure via `ADMIN_EXTENDED` dict in `settings.py`. All keys are optional; defaults shown.

```python
ADMIN_EXTENDED = {
    'MENU_APP_ORDER': [],          # list[str]: sidebar app ordering by app_label
    'MENU_MODEL_ORDER': [],        # list[str]: model ordering within app sections (by object_name)
    'APP_ICON': {},                # dict[str, str]: FontAwesome 5 icon class per app_label
                                   # e.g. {'myapp': 'fas fa-users', 'store': 'fas fa-shopping-cart'}
    'DEFAULT_APP_ICON': 'fas fa-layer-group',  # str: fallback icon for apps not in APP_ICON
    'TABBED_INLINES': True,        # bool: render inlines as tabs
    'AUTO_RAW_ID_FIELDS': False,   # bool: auto-set raw_id/autocomplete on every FK
    'BOOKMARK_CACHE_SECONDS': 60,  # int: how long to cache the bookmark sidebar entry
}
```

Settings are read lazily via `admin_extended.conf.settings` so `override_settings` works in tests.

---

## Core: ExtendedModelAdmin

The primary base class. Use instead of `admin.ModelAdmin`. Defined at `admin_extended.core.ExtendedModelAdmin`.

```python
from admin_extended.core import ExtendedModelAdmin
from django.contrib import admin

@admin.register(MyModel)
class MyModelAdmin(ExtendedModelAdmin):
    list_display = ('name', 'status', 'owner')
```

### View / Edit / Add modes

Change pages open in **view** (read-only) mode by default. Users switch to edit mode via `?edit=1` in the URL — an "Edit" link appears in the object-tools strip. This is handled automatically by `_changeform_view` and `has_change_permission`.

Page mode helpers (in `admin_extended.core`):

```python
from admin_extended.core import PageMode, current_page_mode, get_page_mode

# PageMode is a StrEnum: PageMode.VIEW, PageMode.EDIT, PageMode.ADD

# Inside any ModelAdmin method called during a changeform request:
mode = current_page_mode()  # PageMode | None — read from ContextVar
if mode is PageMode.EDIT:
    ...

# Classify from request directly (does not depend on ContextVar):
mode = get_page_mode(request, object_id)
```

The active mode is also injected into template context as `ae_page_mode` (string: `'view'`, `'edit'`, or `'add'`).

### Per-mode field visibility

```python
class MyModelAdmin(ExtendedModelAdmin):
    # Hidden in edit/add mode (shown only in view mode).
    # Any field whose name starts with 'display_' is also automatically treated as view-only.
    view_only_fields = ('computed_value',)

    # Hidden in view mode (shown only in edit/add modes).
    edit_only_fields = ('internal_notes',)

    # Hidden from non-superusers (applies to list_display AND fieldsets).
    superuser_only_fields = ('secret_flag',)
```

### Inline tabs

```python
class MyModelAdmin(ExtendedModelAdmin):
    tabbed_inlines = True  # default from settings.TABBED_INLINES
    inlines = [OrderInline, NoteInline]
```

### Auto raw_id / autocomplete on FKs

When `auto_raw_id_fields = True` (or `AUTO_RAW_ID_FIELDS` global), every FK on the model becomes:
- `autocomplete_fields` entry if the target ModelAdmin defines `search_fields`
- `raw_id_fields` entry otherwise

```python
class MyModelAdmin(ExtendedModelAdmin):
    auto_raw_id_fields = True
```

### Delete without confirm

```python
from admin_extended.core.actions import delete_without_confirm

class MyModelAdmin(ExtendedModelAdmin):
    skip_delete_confirm = True  # replaces the default delete_selected action

# Or use the bare action on any admin:
class OtherAdmin(admin.ModelAdmin):
    actions = [delete_without_confirm]
```

---

## Display helpers (admin_extended.display)

### HTML helpers (free functions)

```python
from admin_extended.display import html_img, html_link, html_color, html_json
from admin_extended.display.html import SUCCESS, ERROR, WARNING, DEFAULT

# html_img(url, href=None, height='200px')
def photo(self, obj):
    return html_img(obj.photo_url, height='80px')                # plain <img>
    return html_img(obj.photo_url, href=obj.photo_url)           # <a target="_blank"><img></a>

# html_link(url, title=None, target='_blank', css_class='')
def link(self, obj):
    return html_link(obj.url, title='Open')

# html_color(text, color)  — bold <b style="color:{color}">{text}</b>
def status(self, obj):
    return html_color(obj.get_status_display(), SUCCESS if obj.is_active else ERROR)

# html_json(content, indent=4) — pretty <pre>{json}</pre>
def payload(self, obj):
    return html_json(obj.payload)
```

Color constants in `admin_extended.display.html`: `SUCCESS='#3d9402'`, `ERROR='#f20707'`, `WARNING='#ffad00'`, `DEFAULT='#818181'`.

### FK links in list_display (DisplayLinkAdapter)

Foreign-key field names in `list_display` are automatically rendered as clickable links to the related object's change page (including the `_id` attname variant — `customer` and `customer_id` both work). Built into `ExtendedModelAdmin`. Disable with:

```python
class MyModelAdmin(ExtendedModelAdmin):
    enable_foreign_link = False
```

Skip rules: entry already in `list_display_links`, entry is callable, or entry is not an FK field.

---

## Object Tools

Custom action buttons on change-form / change-list pages.

Decorator: `admin_extended.object_tools.object_tool` — all parameters are keyword-only.

```python
from admin_extended.object_tools import object_tool

@object_tool(
    label='Send invoice',                # required
    icon='fas fa-envelope',              # optional FontAwesome class
    method='GET',                        # 'GET' or 'POST' (uppercase)
    post_param=None,                     # optional; sets the button's name attr for POST tools
    require_permission='change',         # 'change' | 'view' | None
    name=None,                           # optional override for the URL slug (defaults to the function name)
)
def send_invoice(self, request, object_id):
    ...
```

Tool functions receive `(self, request, object_id)` for change-form tools and `(self, request)` for change-list tools. The `object_id` is the string from the URL — call `self.get_object(request, object_id)` to fetch the instance.

Register tools by name on the admin:

```python
from admin_extended.core import ExtendedModelAdmin
from admin_extended.object_tools import object_tool
from django.contrib import admin, messages
from django.http import HttpResponseRedirect
from django.urls import reverse

@admin.register(Order)
class OrderAdmin(ExtendedModelAdmin):
    # GET tools render as links in the object-tools strip (top-right of change form).
    # POST tools render as buttons in the submit row (next to Save).
    change_form_tools = ('send_invoice', 'approve_order')

    # GET tools render on the change list.
    change_list_tools = ('export_csv',)

    @object_tool(label='Send invoice', icon='fas fa-envelope')
    def send_invoice(self, request, object_id):
        obj = self.get_object(request, object_id)
        # ... do work ...
        messages.success(request, f'Invoice sent for #{obj.pk}')
        return HttpResponseRedirect(
            reverse('admin:myapp_order_change', args=[object_id])
        )

    @object_tool(label='Approve', icon='fas fa-check', method='POST')
    def approve_order(self, request, object_id):
        obj = self.get_object(request, object_id)
        # ... do work ...
        return HttpResponseRedirect(
            reverse('admin:myapp_order_change', args=[object_id])
        )

    @object_tool(label='Export CSV', icon='fas fa-download', require_permission=None)
    def export_csv(self, request):
        # ... build response ...
        return response
```

The `ObjectToolMixin` is composed into `ExtendedModelAdmin` — subclassing `ExtendedModelAdmin` is enough. URL routes auto-mount under `<app>/<model>/object-tools/<name>` and `<app>/<model>/<id>/object-tools/<name>`.

---

## DefaultModelAdmin & Auto-registration

`DefaultModelAdmin` extends `ExtendedModelAdmin` and:
- builds `list_display` from all model fields except `id`, `TextField`, and `JSONField` (timestamps `created_at`/`created`/`modified_at`/`modified` moved to the end)
- builds `list_filter` from fields that have `choices`
- adds `select_related` for all relation fields in `get_queryset`

```python
from admin_extended.autoregister import DefaultModelAdmin, auto_register
from django.contrib import admin

# Use for a single model
@admin.register(MyModel)
class MyModelAdmin(DefaultModelAdmin):
    # Override the heuristic if needed:
    list_display_ignore_field_types = (TextField, JSONField, BinaryField)
    list_display_ignore_field_names = ('internal_notes',)

# Or register every model in every non-Django app:
auto_register(
    default_admin=DefaultModelAdmin,         # optional: a subclass of ModelAdmin
    ignore=['myapp.SensitiveModel'],         # 'app_label.ModelName', case-insensitive
    site=admin.site,                         # optional: target AdminSite
)
```

`auto_register` skips any model already registered and any model whose module starts with `django.`.

---

## CustomTableAdminPage

Replace a model's changelist with a fully custom HTML table page. Use a proxy model so the URL slot is reserved.

```python
from admin_extended.custom_pages import CustomTableAdminPage, TableData
from django.contrib import admin

class ReportProxy(MyModel):
    class Meta:
        proxy = True

@admin.register(ReportProxy)
class ReportAdmin(CustomTableAdminPage):
    model = ReportProxy

    def get_table_data(self):
        table = TableData(header='Monthly summary')
        table.titles = ['Month', 'Orders', 'Revenue']
        for row in get_monthly_stats():
            table.add_row([row.month, row.orders, row.revenue])
        return [table]   # multiple TableData allowed; each renders as its own section
```

`TableData` is a dataclass: `TableData(header, titles=[], rows=[])` with `add_row(row: list)`.

---

## Time Series Charts

Database-driven charts created through the Django admin — no chart code needed.

Requires `admin_extended.charts` in `INSTALLED_APPS`.

### Workflow

1. Open **Admin Extended Charts → Time Series Charts** and add a chart.
2. Fill in the chart record (see model fields below).
3. View the chart at `/admin/admin_extended_charts/timeserieschart/<id>/chart/`.
4. JSON metrics endpoint: `/admin/admin_extended_charts/timeserieschart/<id>/metrics/`.

### TimeSeriesChart model (`admin_extended.charts.models.TimeSeriesChart`)

| Field | Type | Notes |
|---|---|---|
| `name` | CharField | Display name |
| `description` | CharField (nullable) | Free-form |
| `chart_type` | `ChartType` | `BAR` or `LINE` |
| `stacked` | bool | Stack series (multi-series only) |
| `target_app_label` | str | App label of source model |
| `target_model_name` | str | Model name (case-insensitive) |
| `time_field` | str | DateTimeField name on the target — the bucket axis |
| `aggregate` | `Aggregate` | `COUNT` / `SUM` / `AVG` / `MIN` / `MAX` |
| `aggregate_field` | str | Field to aggregate; `'*'` only valid for COUNT |
| `aggregate_label` | str | Series label shown in the chart legend (single-series mode) |
| `split_field` | str (nullable) | Group rows by this field → one series per distinct value |
| `filter_field` | str (nullable) | Expose this field as a dropdown filter on the chart page |
| `filters` | str (nullable) | Static pre-filter as query string, e.g. `status=1&category=3` |
| `default_time_range` | `TimeRange` | `LAST_7_DAY=7` / `LAST_30_DAY=30` / `LAST_YEAR=365` / `ALL_TIME=0` |
| `default_scale` | `Scale` | `HOUR` / `DAY` / `WEEK` / `MONTH` (TruncHour/Day/Week/Month) |
| `max_points` | uint | Cap on returned buckets (default 1000) |
| `cache_seconds` | uint | Per-chart result caching (0 = no cache) |

The model has a `clean()` method that validates `target_model_name`, `time_field`, `aggregate_field`, `split_field`, `filter_field` exist on the target model and parses `filters`.

### Query service (`admin_extended.charts.services`)

```python
from admin_extended.charts.services import ChartQueryService, ChartParams, ChartResult

chart = TimeSeriesChart.objects.get(name='Orders by region')
service = ChartQueryService(chart)
params = ChartParams(time_range=30, scale='DAY', filter_value=None)
result: ChartResult = service.run_cached(params)
# result.chart_type, result.stacked, result.labels: list[str], result.datasets: list[ChartSeries]
```

### Metrics URL query params

`time_range` (int, days; `0` = all time), `scale` (`HOUR`/`DAY`/`WEEK`/`MONTH`), `filter_value` (only when `filter_field` is set).

---

## Bookmarks

Requires `admin_extended.bookmarks` in `INSTALLED_APPS`. Adds a "Bookmark" group to the top of the admin sidebar, listing active bookmarks ordered by `order`.

Model `admin_extended.bookmarks.models.Bookmark`:

| Field | Type | Notes |
|---|---|---|
| `name` | CharField(45) | Sidebar label |
| `url` | CharField(1000) | Target URL (admin or external) |
| `is_active` | bool | Excluded from sidebar when False |
| `order` | uint | Sort order (asc) |

Manage at **Admin Extended Bookmarks → Bookmarks** using the standard admin change form. Sidebar entries are cached for `ADMIN_EXTENDED['BOOKMARK_CACHE_SECONDS']`; the cache is invalidated automatically on save/delete via signals.

Note: v6 removed the v5 CSRF-disabled POST endpoint (`add_bookmark_view`). There is no inline "+" UI; create bookmarks via the change form.

---

## Template tags

Two libraries are auto-loaded with `{% load admin_extended_menu %}` and `{% load admin_extended_misc %}`.

### `admin_extended_menu`

- `{{ apps|sort_apps }}` — applied to Django's app_list to apply `MENU_APP_ORDER`, attach `icon` from `APP_ICON`, and prepend the cached bookmark group when the bookmarks sub-app is installed.
- `{{ models|sort_models }}` — applied to models in an app group to apply `MENU_MODEL_ORDER`.

### `admin_extended_misc`

- `{% settings_value 'NAME' default %}` — read any setting. Supports dotted paths inside dict settings, e.g. `{% settings_value 'ADMIN_EXTENDED.ADMIN_HEADER_COLOR' 'var(--header-bg)' %}`.

---

## Management commands

```bash
# Print the migration dependency tree for one or more apps.
python manage.py migration_graph myapp otherapp

# Create the database for a configured connection if it does not exist.
# Reads HOST/PORT/USER/PASSWORD/NAME from settings.DATABASES and connects to the
# server's admin database to issue CREATE DATABASE. Idempotent: skips if present.
python manage.py create_db                 # uses the 'default' alias
python manage.py create_db --database analytics
```

Supports the PostgreSQL (`django.db.backends.postgresql`) and MySQL
(`django.db.backends.mysql`) engines only. PostgreSQL requires `psycopg`; MySQL
requires `mysqlclient` or `pymysql`. The connecting user needs `CREATE DATABASE`
privileges. New MySQL databases are created with `utf8mb4` / `utf8mb4_unicode_ci`.

---

## FontAwesome icons

FontAwesome Free 5.15.4 is bundled via the `fontawesomefree` dependency. Use class strings like `fas fa-users`, `far fa-calendar`, `fab fa-github` anywhere the package accepts an `icon` parameter.

**Important:** FontAwesome 6 icon names (e.g. `fa-box-archive`, `fa-bars-staggered`) do not work — use the 5.15 equivalents (`fa-archive`, `fa-stream`).

Icon reference: https://fontawesome.com/v5.15/icons?d=gallery&p=2&m=free

---

## Subsystem layout (for navigating the source)

```
admin_extended/
  conf.py                 # ADMIN_EXTENDED settings proxy
  core/                   # ExtendedModelAdmin, PageMode, field_visibility, actions
  display/                # html_* helpers, color constants, DisplayLinkAdapter
  object_tools/           # @object_tool decorator, ObjectToolMixin, views
  autoregister/           # DefaultModelAdmin, auto_register
  custom_pages/           # CustomTableAdminPage, TableData
  bookmarks/              # sub-app: Bookmark model + admin
  charts/                 # sub-app: TimeSeriesChart, ChartQueryService, views, forms
  templatetags/           # admin_extended_menu, admin_extended_misc
  templates/admin/        # base_site, change_form, change_list, app_list overrides
  management/commands/    # migration_graph, create_db
```
