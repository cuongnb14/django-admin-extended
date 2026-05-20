# django-admin-extended v6 Refactor Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Refactor `django-admin-extended` from v5.1.6 to v6.0.0 — a hard-break re-architecture that preserves all features but restructures the codebase into feature-bounded subsystems, fixes documented bugs, and modernizes tooling.

**Architecture:** Subsystem-oriented layout. `core`, `display`, `object_tools`, `autoregister`, `custom_pages`, `management` as Python sub-packages. `bookmarks` and `charts` as separate Django sub-apps (must be added to `INSTALLED_APPS`). Theme assets (templates, static, templatetags) live at the `admin_extended/` root so Django auto-discovery works.

**Tech Stack:** Python 3.12+, Django 5.2 LTS or Django 6.0+, pytest 8 + pytest-django + pytest-cov, tox 4, ruff, mypy strict, setuptools 68 + setuptools-scm.

**Reference:** Full design rationale is in `docs/superpowers/specs/2026-05-20-v6-architecture-refactor-design.md`. This plan implements that spec.

---

## Strategy

v5 source files stay in place during the refactor; new v6 modules are created in their new locations alongside v5. The old `admin_extended/base/`, `admin_extended/admin/`, `admin_extended/models/`, and `admin_extended/utils.py` are deleted in Phase 14 once all new subsystems exist and pass tests. This keeps the codebase importable at every commit so CI never fails on intermediate states.

Each phase is one logical commit boundary. Within a phase, each task is a TDD micro-cycle: write failing test → implement → run test → commit.

---

## File Structure

```
admin_extended/
  __init__.py
  apps.py                       # AdminExtendedConfig
  conf.py                       # AdminExtendedSettings (lazy proxy)
  py.typed                      # PEP 561 marker

  templates/admin/              # auto-discovered
    base_site.html              # theme
    change_form.html            # theme
    change_list.html            # theme
    app_list.html               # theme
    search_form.html            # theme
    admin_extended/
      object_tools/
        change_form_object_tools.html
        change_form_submit_row.html
      custom_pages/
        custom_table_page.html

  static/admin_extended/css/    # auto-discovered

  templatetags/
    __init__.py
    admin_extended_menu.py
    admin_extended_misc.py

  core/
    __init__.py
    page_mode.py
    field_visibility.py
    model_admin.py
    actions.py

  object_tools/
    __init__.py
    decorator.py
    mixin.py
    views.py

  display/
    __init__.py
    link_adapter.py
    html.py

  autoregister/
    __init__.py
    default_admin.py
    registry.py

  custom_pages/
    __init__.py
    table_page.py

  bookmarks/                    # Django sub-app
    __init__.py
    apps.py
    models.py
    admin.py
    forms.py
    migrations/0001_initial.py
    templates/admin/admin_extended/bookmarks/

  charts/                       # Django sub-app
    __init__.py
    apps.py
    models.py
    services.py
    forms.py
    admin.py
    views.py
    urls.py
    migrations/0001_initial.py
    templates/admin/admin_extended/charts/chart.html

  management/
    __init__.py
    commands/__init__.py
    commands/migration_graph.py

  tests/                        # excluded from wheel
    __init__.py
    conftest.py
    example_project/
      __init__.py
      settings.py
      urls.py
      sample_app/
        __init__.py
        apps.py
        models.py
        admin.py
        migrations/0001_initial.py
    test_conf.py
    test_core_page_mode.py
    test_core_field_visibility.py
    test_core_model_admin.py
    test_display_html.py
    test_display_link.py
    test_object_tools.py
    test_autoregister.py
    test_custom_pages.py
    test_bookmarks.py
    test_charts_models.py
    test_charts_service.py
    test_charts_form.py
    test_charts_views.py
    test_theme_menu.py
    test_management_migration_graph.py
    test_imports.py
```

Files deleted at end:
- `setup.py`, `MANIFEST.in`, `README.rst` (replaced by `pyproject.toml`, `README.md`)
- `admin_extended/base/`, `admin_extended/admin/`, `admin_extended/models/`, `admin_extended/utils.py`, `admin_extended/decorators.py`, `admin_extended/settings.py`, `admin_extended/templatetags/sort_menu_items.py`, `admin_extended/templatetags/settings_value.py`
- Migrations: `admin_extended/migrations/0001_initial.py`, `0002_timeserieschart.py`

---

## Phase 1: Foundation

Establishes `pyproject.toml`, tox, CI, the test scaffolding, and an `example_project` Django config that test modules use as `DJANGO_SETTINGS_MODULE`. v5 code is left untouched.

### Task 1.1: Delete legacy build files

**Files:**
- Delete: `setup.py`
- Delete: `MANIFEST.in`
- Delete: `README.rst`

- [ ] **Step 1: Remove the files**

```bash
git rm setup.py MANIFEST.in README.rst
```

- [ ] **Step 2: Verify**

```bash
ls setup.py MANIFEST.in README.rst 2>&1
```

Expected: `ls: setup.py: No such file or directory` (and same for the others).

### Task 1.2: Create pyproject.toml

**Files:**
- Create: `pyproject.toml`

- [ ] **Step 1: Write the file**

```toml
[build-system]
requires = ["setuptools>=68", "setuptools-scm>=8"]
build-backend = "setuptools.build_meta"

[project]
name = "django-admin-extended"
dynamic = ["version"]
description = "Enhance UI/UX of Django admin"
readme = "README.md"
requires-python = ">=3.12"
license = { text = "MIT" }
authors = [{ name = "Cuong Nguyen", email = "cuongnb14@gmail.com" }]
keywords = ["django", "admin", "ui", "ux"]
classifiers = [
    "Environment :: Web Environment",
    "Framework :: Django",
    "Framework :: Django :: 5.2",
    "Framework :: Django :: 6.0",
    "Intended Audience :: Developers",
    "License :: OSI Approved :: MIT License",
    "Operating System :: OS Independent",
    "Programming Language :: Python :: 3 :: Only",
    "Programming Language :: Python :: 3.12",
    "Programming Language :: Python :: 3.13",
    "Topic :: Internet :: WWW/HTTP :: Dynamic Content",
]
dependencies = [
    "Django>=5.2,<7.0",
    "fontawesomefree==5.15.4",
]

[project.optional-dependencies]
test = [
    "pytest>=8",
    "pytest-django>=4.8",
    "pytest-cov>=5",
]
dev = [
    "django-admin-extended[test]",
    "ruff>=0.6",
    "mypy>=1.11",
    "django-stubs[compatible-mypy]>=5.1",
    "tox>=4",
    "build>=1.2",
]

[project.urls]
Homepage = "https://github.com/cuongnb14/django-admin-extended"
Issues = "https://github.com/cuongnb14/django-admin-extended/issues"
Changelog = "https://github.com/cuongnb14/django-admin-extended/blob/main/CHANGELOG.md"

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
extend-exclude = ["**/migrations/*.py"]

[tool.ruff.lint]
select = ["E", "F", "I", "UP", "B", "DJ", "RUF", "SIM"]

[tool.mypy]
python_version = "3.12"
strict = true
plugins = ["mypy_django_plugin.main"]
exclude = ["admin_extended/tests/.*", "admin_extended/.*/migrations/.*"]

[tool.django-stubs]
django_settings_module = "admin_extended.tests.example_project.settings"

[tool.pytest.ini_options]
DJANGO_SETTINGS_MODULE = "admin_extended.tests.example_project.settings"
python_files = ["test_*.py"]
addopts = "-ra --strict-markers"

[tool.coverage.run]
branch = true
source = ["admin_extended"]
omit = ["admin_extended/tests/*", "admin_extended/*/migrations/*", "admin_extended/_version.py"]
```

- [ ] **Step 2: Verify it parses**

```bash
python -c "import tomllib; tomllib.load(open('pyproject.toml','rb'))"
```

Expected: exit code 0, no output.

### Task 1.3: Create tox.ini

**Files:**
- Create: `tox.ini`

- [ ] **Step 1: Write the file**

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

### Task 1.4: Update .gitignore

**Files:**
- Modify: `.gitignore`

- [ ] **Step 1: Append v6 artifacts**

Append these lines to `.gitignore`:

```
# v6 build artifacts
admin_extended/_version.py
dist/
*.egg-info/
.tox/
.pytest_cache/
.coverage
htmlcov/
.mypy_cache/
.ruff_cache/
__pycache__/
```

- [ ] **Step 2: Verify**

```bash
grep -E "_version\.py|\.tox" .gitignore
```

Expected: both patterns matched.

### Task 1.5: Create README.md placeholder

**Files:**
- Create: `README.md`

- [ ] **Step 1: Write minimal content**

```markdown
# django-admin-extended

Enhance UI/UX of Django admin.

## Installation

```bash
pip install "git+https://github.com/cuongnb14/django-admin-extended.git@v6.0.0"
```

Add to `INSTALLED_APPS`:

```python
INSTALLED_APPS = [
    'admin_extended',                  # required
    'admin_extended.bookmarks',        # optional
    'admin_extended.charts',           # optional
    # ...
]
```

See `CHANGELOG.md` for the full feature list and v5 → v6 migration notes.
```

The README will be expanded in Phase 14.

### Task 1.6: Create py.typed marker

**Files:**
- Create: `admin_extended/py.typed`

- [ ] **Step 1: Create empty marker file**

```bash
touch admin_extended/py.typed
```

### Task 1.7: Create tests scaffolding

**Files:**
- Create: `admin_extended/tests/__init__.py`
- Create: `admin_extended/tests/example_project/__init__.py`
- Create: `admin_extended/tests/example_project/settings.py`
- Create: `admin_extended/tests/example_project/urls.py`

- [ ] **Step 1: Create empty __init__ files**

```bash
mkdir -p admin_extended/tests/example_project
touch admin_extended/tests/__init__.py
touch admin_extended/tests/example_project/__init__.py
```

- [ ] **Step 2: Write `example_project/settings.py`**

```python
"""Minimal Django settings used by the pytest suite."""
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

SECRET_KEY = "test-secret-key-not-for-production"
DEBUG = True
ALLOWED_HOSTS = ["*"]

INSTALLED_APPS = [
    "django.contrib.contenttypes",
    "django.contrib.auth",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.admin",
    "django.contrib.staticfiles",
    "admin_extended",
    "admin_extended.bookmarks",
    "admin_extended.charts",
    "admin_extended.tests.example_project.sample_app",
]

MIDDLEWARE = [
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
]

ROOT_URLCONF = "admin_extended.tests.example_project.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    }
}

STATIC_URL = "/static/"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
USE_TZ = True

ADMIN_EXTENDED = {}
```

- [ ] **Step 3: Write `example_project/urls.py`**

```python
from django.contrib import admin
from django.urls import path

urlpatterns = [
    path("admin/", admin.site.urls),
]
```

- [ ] **Step 4: Write `conftest.py`**

Create `admin_extended/tests/conftest.py`:

```python
"""Shared pytest fixtures."""
from __future__ import annotations

import pytest
from django.contrib.auth import get_user_model
from django.test import Client


@pytest.fixture
def user(db):
    User = get_user_model()
    return User.objects.create_user(
        username="staff",
        password="pw",
        is_staff=True,
    )


@pytest.fixture
def superuser(db):
    User = get_user_model()
    return User.objects.create_superuser(
        username="root",
        password="pw",
        email="root@example.com",
    )


@pytest.fixture
def admin_client(superuser):
    client = Client()
    client.force_login(superuser)
    return client
```

### Task 1.8: Create sample_app for tests

**Files:**
- Create: `admin_extended/tests/example_project/sample_app/__init__.py`
- Create: `admin_extended/tests/example_project/sample_app/apps.py`
- Create: `admin_extended/tests/example_project/sample_app/models.py`
- Create: `admin_extended/tests/example_project/sample_app/migrations/__init__.py`
- Create: `admin_extended/tests/example_project/sample_app/migrations/0001_initial.py`

- [ ] **Step 1: Create directories and stubs**

```bash
mkdir -p admin_extended/tests/example_project/sample_app/migrations
touch admin_extended/tests/example_project/sample_app/__init__.py
touch admin_extended/tests/example_project/sample_app/migrations/__init__.py
```

- [ ] **Step 2: Write apps.py**

```python
from django.apps import AppConfig


class SampleAppConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "admin_extended.tests.example_project.sample_app"
    label = "sample_app"
```

- [ ] **Step 3: Write models.py**

```python
from django.db import models


class Customer(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField()

    class Meta:
        app_label = "sample_app"

    def __str__(self) -> str:
        return self.name


class Product(models.Model):
    STATUS_CHOICES = [("draft", "Draft"), ("active", "Active"), ("archived", "Archived")]
    name = models.CharField(max_length=100)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="draft")
    notes = models.TextField(blank=True, default="")

    class Meta:
        app_label = "sample_app"

    def __str__(self) -> str:
        return self.name


class Order(models.Model):
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name="orders")
    product = models.ForeignKey(Product, on_delete=models.PROTECT, related_name="orders")
    quantity = models.PositiveIntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)
    region = models.CharField(max_length=50, blank=True, default="")

    class Meta:
        app_label = "sample_app"
```

- [ ] **Step 4: Write migration 0001_initial.py**

```python
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    initial = True
    dependencies = []
    operations = [
        migrations.CreateModel(
            name="Customer",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                ("name", models.CharField(max_length=100)),
                ("email", models.EmailField(max_length=254)),
            ],
        ),
        migrations.CreateModel(
            name="Product",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                ("name", models.CharField(max_length=100)),
                ("price", models.DecimalField(decimal_places=2, max_digits=10)),
                (
                    "status",
                    models.CharField(
                        choices=[("draft", "Draft"), ("active", "Active"), ("archived", "Archived")],
                        default="draft",
                        max_length=20,
                    ),
                ),
                ("notes", models.TextField(blank=True, default="")),
            ],
        ),
        migrations.CreateModel(
            name="Order",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                ("quantity", models.PositiveIntegerField(default=1)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("region", models.CharField(blank=True, default="", max_length=50)),
                ("customer", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="orders", to="sample_app.customer")),
                ("product", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="orders", to="sample_app.product")),
            ],
        ),
    ]
```

### Task 1.9: Create CI workflow

**Files:**
- Create: `.github/workflows/ci.yml`

- [ ] **Step 1: Create directory**

```bash
mkdir -p .github/workflows
```

- [ ] **Step 2: Write ci.yml**

```yaml
name: CI
on:
  push:
    branches: [main, master]
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

### Task 1.10: Verify pytest runs

- [ ] **Step 1: Install dev deps**

```bash
pip install -e ".[dev]"
```

Note: install will succeed even though sub-apps `admin_extended.bookmarks` and `admin_extended.charts` do not yet exist as proper apps — they will fail at Django boot, not at pip install. We address that in step 2.

- [ ] **Step 2: Temporarily comment out sub-app entries in `example_project/settings.py`**

Edit `INSTALLED_APPS` to comment out `admin_extended.bookmarks` and `admin_extended.charts`:

```python
INSTALLED_APPS = [
    "django.contrib.contenttypes",
    "django.contrib.auth",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.admin",
    "django.contrib.staticfiles",
    "admin_extended",
    # "admin_extended.bookmarks",   # enabled in Phase 9
    # "admin_extended.charts",      # enabled in Phase 10
    "admin_extended.tests.example_project.sample_app",
]
```

- [ ] **Step 3: Run pytest**

```bash
pytest
```

Expected: collects 0 tests, exit code 5 (no tests collected) — acceptable. The framework runs.

### Task 1.11: Commit Phase 1

- [ ] **Step 1: Stage and commit**

```bash
git add -A
git commit -m "$(cat <<'EOF'
build: scaffold v6 foundation — pyproject.toml, tox, CI, tests skeleton

Adds PEP 621 packaging with setuptools-scm dynamic versioning, the tox
matrix for Python {3.12,3.13} x Django {5.2,6.0}, GitHub Actions CI
workflow (test, lint, type, build), and the pytest scaffolding with an
example_project + sample_app fixture used by all subsystem tests.

Removes setup.py, MANIFEST.in, README.rst (replaced by pyproject.toml
and README.md). v5 source modules in admin_extended/ are left in place
and will be deleted in Phase 14 as each subsystem is reimplemented.
EOF
)"
```

---

## Phase 2: conf.py — lazy settings proxy

Replaces `admin_extended/settings.py` (module-level frozen dict). The new proxy reads `django.conf.settings.ADMIN_EXTENDED` on every attribute access, so `override_settings` works in tests.

### Task 2.1: Write the failing test

**Files:**
- Create: `admin_extended/tests/test_conf.py`

- [ ] **Step 1: Write test_conf.py**

```python
"""Tests for the lazy settings proxy."""
from __future__ import annotations

import pytest
from django.test import override_settings

from admin_extended.conf import settings as ae_settings


def test_defaults_returned_when_user_did_not_configure():
    assert ae_settings.MENU_APP_ORDER == []
    assert ae_settings.MENU_MODEL_ORDER == []
    assert ae_settings.APP_ICON == {}
    assert ae_settings.TABBED_INLINES is True
    assert ae_settings.AUTO_RAW_ID_FIELDS is False
    assert ae_settings.DEFAULT_APP_ICON == "fas fa-layer-group"
    assert ae_settings.BOOKMARK_CACHE_SECONDS == 60


@override_settings(ADMIN_EXTENDED={"TABBED_INLINES": False, "APP_ICON": {"sample_app": "fas fa-flask"}})
def test_user_overrides_take_precedence():
    assert ae_settings.TABBED_INLINES is False
    assert ae_settings.APP_ICON == {"sample_app": "fas fa-flask"}
    # Unconfigured keys still return defaults
    assert ae_settings.AUTO_RAW_ID_FIELDS is False


def test_override_settings_is_reactive():
    """Changes to settings.ADMIN_EXTENDED at runtime must be observable."""
    assert ae_settings.TABBED_INLINES is True
    with override_settings(ADMIN_EXTENDED={"TABBED_INLINES": False}):
        assert ae_settings.TABBED_INLINES is False
    assert ae_settings.TABBED_INLINES is True


def test_unknown_attribute_raises():
    with pytest.raises(AttributeError):
        ae_settings.DOES_NOT_EXIST
```

- [ ] **Step 2: Run to verify it fails**

```bash
pytest admin_extended/tests/test_conf.py -v
```

Expected: ImportError or ModuleNotFoundError because `admin_extended.conf` does not exist.

### Task 2.2: Implement conf.py

**Files:**
- Create: `admin_extended/conf.py`

- [ ] **Step 1: Write conf.py**

```python
"""Lazy settings proxy.

Reads from ``django.conf.settings.ADMIN_EXTENDED`` on every attribute access,
so ``override_settings`` works correctly during tests.
"""
from __future__ import annotations

from typing import Any

from django.conf import settings as django_settings

_DEFAULTS: dict[str, Any] = {
    "MENU_APP_ORDER": [],
    "MENU_MODEL_ORDER": [],
    "APP_ICON": {},
    "TABBED_INLINES": True,
    "AUTO_RAW_ID_FIELDS": False,
    "DEFAULT_APP_ICON": "fas fa-layer-group",
    "BOOKMARK_CACHE_SECONDS": 60,
}


class AdminExtendedSettings:
    def __getattr__(self, name: str) -> Any:
        if name not in _DEFAULTS:
            raise AttributeError(f"AdminExtendedSettings has no attribute {name!r}")
        user_overrides = getattr(django_settings, "ADMIN_EXTENDED", {})
        return user_overrides.get(name, _DEFAULTS[name])


settings = AdminExtendedSettings()
```

- [ ] **Step 2: Run tests to verify they pass**

```bash
pytest admin_extended/tests/test_conf.py -v
```

Expected: 4 passed.

### Task 2.3: Commit Phase 2

- [ ] **Step 1: Commit**

```bash
git add admin_extended/conf.py admin_extended/tests/test_conf.py
git commit -m "feat(conf): lazy settings proxy reactive to override_settings"
```

---

## Phase 3: core/page_mode.py + core/field_visibility.py

Pure logic with no Django request dependency. Tested first in isolation, then composed into `ExtendedAdminModel` in Phase 5.

### Task 3.1: Write the page_mode test

**Files:**
- Create: `admin_extended/tests/test_core_page_mode.py`

- [ ] **Step 1: Write the tests**

```python
"""Tests for PageMode + ContextVar."""
from __future__ import annotations

from django.test import RequestFactory

from admin_extended.core.page_mode import PageMode, current_page_mode, get_page_mode, page_mode_scope


def test_page_mode_enum_values():
    assert PageMode.VIEW == "view"
    assert PageMode.EDIT == "edit"
    assert PageMode.ADD == "add"


def test_get_page_mode_classifies_add_when_no_object_id():
    request = RequestFactory().get("/admin/sample_app/order/add/")
    assert get_page_mode(request, object_id=None) is PageMode.ADD


def test_get_page_mode_classifies_view_when_object_id_and_no_edit_param():
    request = RequestFactory().get("/admin/sample_app/order/1/change/")
    assert get_page_mode(request, object_id="1") is PageMode.VIEW


def test_get_page_mode_classifies_edit_when_edit_param_set():
    request = RequestFactory().get("/admin/sample_app/order/1/change/?edit=1")
    assert get_page_mode(request, object_id="1") is PageMode.EDIT


def test_get_page_mode_classifies_edit_when_popup_param_set():
    request = RequestFactory().get("/admin/sample_app/order/1/change/?_popup=1")
    assert get_page_mode(request, object_id="1") is PageMode.EDIT


def test_page_mode_scope_sets_and_resets_context_var():
    assert current_page_mode() is None
    with page_mode_scope(PageMode.VIEW):
        assert current_page_mode() is PageMode.VIEW
        with page_mode_scope(PageMode.EDIT):
            assert current_page_mode() is PageMode.EDIT
        assert current_page_mode() is PageMode.VIEW
    assert current_page_mode() is None


def test_page_mode_scope_resets_on_exception():
    try:
        with page_mode_scope(PageMode.VIEW):
            raise RuntimeError("boom")
    except RuntimeError:
        pass
    assert current_page_mode() is None
```

- [ ] **Step 2: Run to verify it fails**

```bash
pytest admin_extended/tests/test_core_page_mode.py -v
```

Expected: ModuleNotFoundError for `admin_extended.core.page_mode`.

### Task 3.2: Implement page_mode.py

**Files:**
- Create: `admin_extended/core/__init__.py`
- Create: `admin_extended/core/page_mode.py`

- [ ] **Step 1: Create core package**

```bash
mkdir -p admin_extended/core
touch admin_extended/core/__init__.py
```

- [ ] **Step 2: Write page_mode.py**

```python
"""Page mode (view / edit / add) for the admin changeform.

Implemented via ``contextvars.ContextVar`` so the request object is never
mutated. ``ExtendedAdminModel._changeform_view`` enters ``page_mode_scope``
at the start of every request and exits it in a ``finally`` block.
"""
from __future__ import annotations

from contextlib import contextmanager
from contextvars import ContextVar
from enum import StrEnum
from typing import Iterator

from django.http import HttpRequest


class PageMode(StrEnum):
    VIEW = "view"
    EDIT = "edit"
    ADD = "add"


_page_mode_var: ContextVar[PageMode | None] = ContextVar("admin_extended_page_mode", default=None)


def current_page_mode() -> PageMode | None:
    """Return the page mode set by the active ``page_mode_scope``, or None."""
    return _page_mode_var.get()


@contextmanager
def page_mode_scope(mode: PageMode) -> Iterator[None]:
    """Set the page mode for the duration of the with-block."""
    token = _page_mode_var.set(mode)
    try:
        yield
    finally:
        _page_mode_var.reset(token)


def get_page_mode(request: HttpRequest, object_id: str | int | None) -> PageMode:
    """Classify the page mode from request + object_id.

    ADD when no object_id; EDIT when ``?edit=`` or ``?_popup=`` present; VIEW otherwise.
    """
    if object_id is None:
        return PageMode.ADD
    if "edit" in request.GET or "_popup" in request.GET:
        return PageMode.EDIT
    return PageMode.VIEW
```

- [ ] **Step 3: Run tests to verify pass**

```bash
pytest admin_extended/tests/test_core_page_mode.py -v
```

Expected: 7 passed.

### Task 3.3: Write the field_visibility test

**Files:**
- Create: `admin_extended/tests/test_core_field_visibility.py`

- [ ] **Step 1: Write tests**

```python
"""Tests for fieldset-filtering helpers."""
from __future__ import annotations

from admin_extended.core.field_visibility import (
    filter_fieldsets,
    is_display_only,
)


def _sample_fieldsets():
    return [
        (None, {"fields": ("name", "status", "display_summary", "internal_notes")}),
        ("Meta", {"fields": (("created_at", "modified_at"), "secret_flag")}),
    ]


def test_is_display_only_true_for_display_prefix():
    assert is_display_only("display_summary", read_only_fields=set())
    assert is_display_only("display_anything", read_only_fields=set())


def test_is_display_only_true_for_explicit_read_only():
    assert is_display_only("summary", read_only_fields={"summary"})


def test_is_display_only_false_for_regular_field():
    assert not is_display_only("name", read_only_fields=set())


def test_filter_fieldsets_removes_by_predicate():
    fieldsets = _sample_fieldsets()
    result = filter_fieldsets(fieldsets, lambda f: f in {"secret_flag", "display_summary"})

    assert result == [
        (None, {"fields": ("name", "status", "internal_notes")}),
        ("Meta", {"fields": (("created_at", "modified_at"),)}),
    ]


def test_filter_fieldsets_drops_empty_field_groups():
    fieldsets = [("Meta", {"fields": (("a", "b"),)})]
    result = filter_fieldsets(fieldsets, lambda f: f in {"a", "b"})
    assert result == [("Meta", {"fields": ()})]


def test_filter_fieldsets_does_not_mutate_input():
    fieldsets = _sample_fieldsets()
    snapshot = [(name, dict(opts)) for name, opts in fieldsets]
    filter_fieldsets(fieldsets, lambda f: f in {"secret_flag"})
    for (orig_name, orig_opts), (snap_name, snap_opts) in zip(fieldsets, snapshot):
        assert orig_name == snap_name
        assert orig_opts["fields"] == snap_opts["fields"]
```

- [ ] **Step 2: Run to verify it fails**

```bash
pytest admin_extended/tests/test_core_field_visibility.py -v
```

Expected: ModuleNotFoundError.

### Task 3.4: Implement field_visibility.py

**Files:**
- Create: `admin_extended/core/field_visibility.py`

- [ ] **Step 1: Write the file**

```python
"""Fieldset filtering helpers used by ExtendedAdminModel.

These are pure functions — they do not depend on a request or admin
instance. ExtendedAdminModel composes them into ``get_fieldsets``.
"""
from __future__ import annotations

from collections.abc import Callable, Iterable
from typing import Any

Fieldset = tuple[str | None, dict[str, Any]]


def is_display_only(field_name: str, read_only_fields: Iterable[str]) -> bool:
    """A field is display-only if explicitly listed or its name starts with 'display_'."""
    return field_name in read_only_fields or field_name.startswith("display_")


def filter_fieldsets(
    fieldsets: list[Fieldset] | tuple[Fieldset, ...],
    drop: Callable[[str], bool],
) -> list[Fieldset]:
    """Return a copy of ``fieldsets`` with any field for which ``drop(field)`` is True removed.

    Field entries may be strings or nested tuples/lists. Empty nested groups are dropped.
    The input is not mutated.
    """
    out: list[Fieldset] = []
    for name, opts in fieldsets:
        new_fields: list[Any] = []
        for entry in opts["fields"]:
            if isinstance(entry, str):
                if not drop(entry):
                    new_fields.append(entry)
            else:
                kept = tuple(item for item in entry if not drop(item))
                if kept:
                    new_fields.append(kept)
        new_opts = dict(opts)
        new_opts["fields"] = tuple(new_fields)
        out.append((name, new_opts))
    return out
```

- [ ] **Step 2: Run tests**

```bash
pytest admin_extended/tests/test_core_field_visibility.py -v
```

Expected: 5 passed.

### Task 3.5: Wire core/__init__.py re-exports

**Files:**
- Modify: `admin_extended/core/__init__.py`

- [ ] **Step 1: Add re-exports**

```python
"""Core subsystem: ExtendedAdminModel, page mode, field visibility."""
from .page_mode import PageMode, current_page_mode, get_page_mode, page_mode_scope

__all__ = [
    "PageMode",
    "current_page_mode",
    "get_page_mode",
    "page_mode_scope",
]
```

`ExtendedAdminModel` will be added to `__all__` in Phase 5 once implemented.

### Task 3.6: Commit Phase 3

```bash
git add admin_extended/core admin_extended/tests/test_core_page_mode.py admin_extended/tests/test_core_field_visibility.py
git commit -m "feat(core): add PageMode ContextVar + pure fieldset filter helpers"
```

---

## Phase 4: display/ subsystem

HTML helpers as free functions + `DisplayLinkAdapter` (typo fixed, B7 regression covered).

### Task 4.1: Test html helpers

**Files:**
- Create: `admin_extended/tests/test_display_html.py`

- [ ] **Step 1: Write tests**

```python
"""Tests for free HTML helper functions."""
from __future__ import annotations

from django.utils.safestring import SafeString

from admin_extended.display import html_color, html_img, html_json, html_link
from admin_extended.display.html import DEFAULT, ERROR, SUCCESS, WARNING


def test_html_img_returns_safe_html():
    out = html_img("https://example.com/a.png", height="40px")
    assert isinstance(out, SafeString)
    assert 'src="https://example.com/a.png"' in out
    assert 'height="40px"' in out


def test_html_img_returns_dash_for_empty_url():
    assert html_img("") == "-"
    assert html_img(None) == "-"


def test_html_img_with_href_wraps_in_anchor():
    out = html_img("https://x/i.png", href="https://x/page")
    assert '<a href="https://x/page"' in out
    assert "<img" in out


def test_html_link_uses_url_as_title_when_omitted():
    out = html_link("https://x")
    assert ">https://x<" in out


def test_html_link_uses_custom_title():
    out = html_link("https://x", title="Click")
    assert ">Click<" in out


def test_html_color_renders_bold_with_color():
    out = html_color("OK", SUCCESS)
    assert "<b" in out and ">OK<" in out and "color:#3d9402" in out


def test_html_json_pretty_prints_in_pre():
    out = html_json({"a": 1, "b": [2, 3]})
    assert out.startswith("<pre>")
    assert '"a": 1' in out


def test_color_constants_are_strings():
    assert all(isinstance(c, str) for c in (SUCCESS, ERROR, WARNING, DEFAULT))
```

- [ ] **Step 2: Run to verify it fails**

```bash
pytest admin_extended/tests/test_display_html.py -v
```

Expected: ModuleNotFoundError for `admin_extended.display`.

### Task 4.2: Implement display/html.py

**Files:**
- Create: `admin_extended/display/__init__.py`
- Create: `admin_extended/display/html.py`

- [ ] **Step 1: Write display/html.py**

```python
"""HTML rendering helpers for admin display methods."""
from __future__ import annotations

import json
from typing import Any

from django.utils.html import format_html
from django.utils.safestring import SafeString

SUCCESS = "#3d9402"
ERROR = "#f20707"
WARNING = "#ffad00"
DEFAULT = "#818181"


def html_img(url: str | None, href: str | None = None, height: str = "200px") -> SafeString | str:
    """Return an <img> tag, optionally wrapped in <a>, or '-' if url is falsy."""
    if not url:
        return "-"
    if href:
        return format_html('<a href="{}" target="_blank"><img height="{}" src="{}" /></a>', href, height, url)
    return format_html('<img height="{}" src="{}" />', height, url)


def html_link(url: str, title: str | None = None, target: str = "_blank", css_class: str = "") -> SafeString:
    """Return an <a> tag; if title is omitted, the URL itself is the visible text."""
    visible = title if title is not None else url
    return format_html('<a href="{}" class="{}" target="{}">{}</a>', url, css_class, target, visible)


def html_color(text: str, color: str) -> SafeString:
    """Return a bold-colored span around the text."""
    return format_html('<b style="color:{};">{}</b>', color, text)


def html_json(content: Any, indent: int = 4) -> SafeString:
    """Pretty-print JSON inside a <pre> tag."""
    return format_html("<pre>{}</pre>", json.dumps(content, indent=indent, default=str))
```

- [ ] **Step 2: Write display/__init__.py**

```python
"""Display subsystem: HTML helpers + FK link adapter."""
from .html import html_color, html_img, html_json, html_link

__all__ = ["html_color", "html_img", "html_json", "html_link"]
```

(`DisplayLinkAdapter` will be added to `__all__` in Task 4.4.)

- [ ] **Step 3: Run tests**

```bash
pytest admin_extended/tests/test_display_html.py -v
```

Expected: 8 passed.

### Task 4.3: Test DisplayLinkAdapter

**Files:**
- Create: `admin_extended/tests/test_display_link.py`

- [ ] **Step 1: Write tests**

```python
"""Tests for the FK list_display link adapter (covers B7 regression)."""
from __future__ import annotations

from django.contrib import admin
from django.test import RequestFactory

from admin_extended.display import DisplayLinkAdapter
from admin_extended.tests.example_project.sample_app.models import Customer, Order


class _DummyAdmin(DisplayLinkAdapter, admin.ModelAdmin):
    model = Order

    def get_list_display(self, request):
        return self.list_display


def test_fk_field_converted_to_link_when_not_in_list_display_links(admin_site=None):
    site = admin.AdminSite(name="dummy")
    site.register(Customer)
    site.register(Order, _DummyAdmin)
    order_admin = site._registry[Order]
    order_admin.list_display = ("id", "customer", "product", "quantity")
    order_admin.list_display_links = ("id",)

    request = RequestFactory().get("/")
    result = order_admin.get_list_display(request)

    # customer and product are FKs, NOT in list_display_links -> converted to callables
    assert callable(result[1])
    assert callable(result[2])
    # id is in list_display_links -> kept as string
    assert result[0] == "id"
    # quantity is not FK -> kept as string
    assert result[3] == "quantity"


def test_does_not_skip_first_element_b7_regression():
    """v5 used list_display[0] unconditionally; v6 must process index 0 too."""
    site = admin.AdminSite(name="dummy2")
    site.register(Customer)
    site.register(Order, _DummyAdmin)
    order_admin = site._registry[Order]
    # customer is at index 0 AND not in list_display_links -> must become callable
    order_admin.list_display = ("customer", "quantity")
    order_admin.list_display_links = ()

    request = RequestFactory().get("/")
    result = order_admin.get_list_display(request)
    assert callable(result[0])


def test_enable_foreign_link_false_skips_conversion():
    site = admin.AdminSite(name="dummy3")
    site.register(Customer)

    class A(DisplayLinkAdapter, admin.ModelAdmin):
        model = Order
        enable_foreign_link = False
        list_display = ("customer", "quantity")
        list_display_links = ()

        def get_list_display(self, request):
            return self.list_display

    site.register(Order, A)
    admin_inst = site._registry[Order]
    request = RequestFactory().get("/")
    result = admin_inst.get_list_display(request)
    assert result == ("customer", "quantity")
```

- [ ] **Step 2: Run to verify it fails**

```bash
pytest admin_extended/tests/test_display_link.py -v
```

Expected: ImportError because `DisplayLinkAdapter` is not yet in `admin_extended.display`.

### Task 4.4: Implement DisplayLinkAdapter

**Files:**
- Create: `admin_extended/display/link_adapter.py`
- Modify: `admin_extended/display/__init__.py`

- [ ] **Step 1: Write link_adapter.py**

```python
"""Adapter that converts FK fields in list_display to clickable links."""
from __future__ import annotations

from collections.abc import Callable
from typing import Any

from django.contrib import admin
from django.db.models import ForeignKey
from django.urls import reverse
from django.utils.html import format_html


class DisplayLinkAdapter:
    """Mixin for ModelAdmin that turns FK columns into change-page links.

    Skip rules (NOT converted to links):
      * field already in ``list_display_links``
      * entry is callable
      * field is not a ForeignKey
      * ``enable_foreign_link`` is False
    """

    enable_foreign_link: bool = True

    def _foreign_key_link(self, field_name: str, verbose_name: str) -> Callable[[Any], Any]:
        def display_fn(obj: Any) -> Any:
            linked = getattr(obj, field_name)
            if linked is None:
                return "-"
            app_label = linked._meta.app_label
            model_name = linked._meta.model_name
            url = reverse(f"admin:{app_label}_{model_name}_change", args=[linked.pk])
            return format_html('<a href="{}">{}</a>', url, linked)

        display_fn.short_description = verbose_name  # type: ignore[attr-defined]
        return display_fn

    def _fk_field_map(self) -> dict[str, str]:
        """Return a map of {fk_field_name: verbose_name} for the admin's model.

        Both the actual field name (``customer``) and the attname (``customer_id``)
        map to the same entry so consumers can write either in list_display.
        """
        out: dict[str, str] = {}
        for field in self.model._meta.fields:  # type: ignore[attr-defined]
            if isinstance(field, ForeignKey):
                out[field.name] = str(field.verbose_name)
                out[field.attname] = str(field.verbose_name)
        return out

    def _should_link(self, entry: Any, fk_map: dict[str, str], list_display_links: tuple[str, ...]) -> bool:
        if not self.enable_foreign_link:
            return False
        if not isinstance(entry, str):
            return False
        if entry in list_display_links:
            return False
        return entry in fk_map

    def get_list_display(self, request: Any) -> tuple[Any, ...]:
        list_display = tuple(super().get_list_display(request))  # type: ignore[misc]
        list_display_links = tuple(getattr(self, "list_display_links", ()) or ())
        fk_map = self._fk_field_map()

        out: list[Any] = []
        for entry in list_display:
            if self._should_link(entry, fk_map, list_display_links):
                out.append(self._foreign_key_link(entry, fk_map[entry]))
            else:
                out.append(entry)
        return tuple(out)
```

- [ ] **Step 2: Update display/__init__.py**

```python
"""Display subsystem: HTML helpers + FK link adapter."""
from .html import html_color, html_img, html_json, html_link
from .link_adapter import DisplayLinkAdapter

__all__ = ["DisplayLinkAdapter", "html_color", "html_img", "html_json", "html_link"]
```

- [ ] **Step 3: Run tests**

```bash
pytest admin_extended/tests/test_display_link.py -v
```

Expected: 3 passed.

### Task 4.5: Commit Phase 4

```bash
git add admin_extended/display admin_extended/tests/test_display_html.py admin_extended/tests/test_display_link.py
git commit -m "feat(display): free HTML helpers + DisplayLinkAdapter (typo + B7 fix)"
```

---

## Phase 5: core/model_admin.py — ExtendedAdminModel

Composes page_mode, field_visibility, DisplayLinkAdapter. This is the user-facing base class.

### Task 5.1: Test view-mode read-only behavior

**Files:**
- Create: `admin_extended/tests/test_core_model_admin.py`

- [ ] **Step 1: Write tests**

```python
"""Integration tests for ExtendedAdminModel using sample_app."""
from __future__ import annotations

from django.contrib import admin
from django.test import RequestFactory

from admin_extended.core import ExtendedAdminModel, PageMode, get_page_mode
from admin_extended.tests.example_project.sample_app.models import Customer, Order, Product


def _site_with(*models_admins):
    site = admin.AdminSite(name=f"test_{id(models_admins)}")
    for model, model_admin_cls in models_admins:
        site.register(model, model_admin_cls)
    return site


def test_view_mode_has_change_permission_is_false(superuser):
    class ProductAdmin(ExtendedAdminModel):
        pass

    site = _site_with((Product, ProductAdmin))
    pa = site._registry[Product]

    request = RequestFactory().get("/admin/sample_app/product/1/change/")
    request.user = superuser
    product = Product(name="x", price=1)

    # In view mode (no ?edit) the admin must report no change permission.
    assert get_page_mode(request, object_id=1) is PageMode.VIEW
    assert pa.has_change_permission(request, product) is False


def test_edit_mode_has_change_permission_is_true(superuser):
    class ProductAdmin(ExtendedAdminModel):
        pass

    site = _site_with((Product, ProductAdmin))
    pa = site._registry[Product]

    request = RequestFactory().get("/admin/sample_app/product/1/change/?edit=1")
    request.user = superuser
    product = Product(name="x", price=1)

    assert get_page_mode(request, object_id=1) is PageMode.EDIT
    assert pa.has_change_permission(request, product) is True


def test_super_admin_only_fields_hidden_from_non_superuser(user):
    class ProductAdmin(ExtendedAdminModel):
        list_display = ("name", "price", "status")
        superuser_only_fields = ("status",)

    site = _site_with((Product, ProductAdmin))
    pa = site._registry[Product]

    request = RequestFactory().get("/")
    request.user = user  # staff but not superuser
    assert "status" not in pa.get_list_display(request)


def test_super_admin_only_fields_visible_to_superuser(superuser):
    class ProductAdmin(ExtendedAdminModel):
        list_display = ("name", "price", "status")
        superuser_only_fields = ("status",)

    site = _site_with((Product, ProductAdmin))
    pa = site._registry[Product]

    request = RequestFactory().get("/")
    request.user = superuser
    assert "status" in pa.get_list_display(request)
```

- [ ] **Step 2: Run to verify it fails**

```bash
pytest admin_extended/tests/test_core_model_admin.py -v
```

Expected: ImportError — `ExtendedAdminModel` not in `admin_extended.core`.

### Task 5.2: Implement core/actions.py

**Files:**
- Create: `admin_extended/core/actions.py`

- [ ] **Step 1: Write actions.py**

```python
"""Reusable admin actions."""
from __future__ import annotations

from django.contrib import admin, messages


@admin.action(description="Delete selected without confirm")
def delete_without_confirm(modeladmin, request, queryset):  # noqa: ARG001
    deleted, _ = queryset.delete()
    messages.success(request, f"Deleted {deleted} record(s)")
```

### Task 5.3: Implement core/model_admin.py

**Files:**
- Create: `admin_extended/core/model_admin.py`
- Modify: `admin_extended/core/__init__.py`

- [ ] **Step 1: Write model_admin.py**

```python
"""ExtendedAdminModel — the main base class consumers subclass.

Composes:
  * ``DisplayLinkAdapter``  -> FK columns become links
  * Fieldset filtering by ``PageMode`` and ``superuser_only_fields``
  * View / Edit / Add page-mode classification via ``ContextVar``
  * Tabbed inlines (``tabbed_inlines``)
  * Auto raw_id/autocomplete (``auto_raw_id_fields``)
  * Optional ``skip_delete_confirm`` action override
"""
from __future__ import annotations

from collections.abc import Iterable
from typing import Any

from django.contrib import admin
from django.http import HttpRequest

from ..conf import settings as ae_settings
from ..display.link_adapter import DisplayLinkAdapter
from .actions import delete_without_confirm
from .field_visibility import filter_fieldsets, is_display_only
from .page_mode import PageMode, get_page_mode, page_mode_scope


def _has_search_fields(field) -> bool:  # type: ignore[no-untyped-def]
    model_admin = admin.site._registry.get(field.related_model)
    return bool(model_admin and model_admin.search_fields)


class ExtendedAdminModel(DisplayLinkAdapter, admin.ModelAdmin):
    """Drop-in replacement for ``admin.ModelAdmin`` with v6 features.

    Class attributes:
        view_only_fields:        fields shown only in VIEW mode
        edit_only_fields:        fields shown only in EDIT / ADD mode
        superuser_only_fields:   fields hidden from non-superusers (both list & form)
        tabbed_inlines:          render inlines as tabs (default from settings)
        skip_delete_confirm:     replace delete_selected with no-confirm variant
        auto_raw_id_fields:      auto-set autocomplete/raw_id for all FKs
    """

    view_only_fields: tuple[str, ...] = ()
    edit_only_fields: tuple[str, ...] = ()
    superuser_only_fields: tuple[str, ...] = ()

    tabbed_inlines: bool = True
    skip_delete_confirm: bool = False
    auto_raw_id_fields: bool = False

    def __init__(self, model, admin_site) -> None:  # type: ignore[no-untyped-def]
        # Pull settings-backed defaults *at instantiation*, not import time,
        # so override_settings in tests is honored.
        if type(self).tabbed_inlines is True and "tabbed_inlines" not in type(self).__dict__:
            self.tabbed_inlines = ae_settings.TABBED_INLINES
        if type(self).auto_raw_id_fields is False and "auto_raw_id_fields" not in type(self).__dict__:
            self.auto_raw_id_fields = ae_settings.AUTO_RAW_ID_FIELDS

        if self.auto_raw_id_fields:
            self.autocomplete_fields, self.raw_id_fields = self._compute_raw_id_fields(model)

        super().__init__(model, admin_site)

    @staticmethod
    def _compute_raw_id_fields(model) -> tuple[tuple[str, ...], tuple[str, ...]]:  # type: ignore[no-untyped-def]
        ac = tuple(f.name for f in model._meta.fields if f.is_relation and _has_search_fields(f))
        ri = tuple(f.name for f in model._meta.fields if f.is_relation and not _has_search_fields(f))
        return ac, ri

    # ---- page mode integration ----------------------------------------

    def _changeform_view(self, request, object_id, form_url, extra_context):  # type: ignore[no-untyped-def]
        mode = get_page_mode(request, object_id)
        with page_mode_scope(mode):
            return super()._changeform_view(request, object_id, form_url, extra_context)

    def has_change_permission(self, request: HttpRequest, obj: Any = None) -> bool:
        # object_id detection mirrors Django: present in URL kwargs as 'object_id' or path
        object_id = obj.pk if obj is not None else None
        if object_id is not None and get_page_mode(request, object_id) is PageMode.VIEW:
            return False
        return super().has_change_permission(request, obj)

    # ---- fieldset filtering -------------------------------------------

    def get_fieldsets(self, request: HttpRequest, obj: Any = None):  # type: ignore[no-untyped-def]
        fieldsets = list(super().get_fieldsets(request, obj))
        mode = get_page_mode(request, object_id=(obj.pk if obj is not None else None))
        fieldsets = self._filter_by_mode(mode, fieldsets)
        fieldsets = self._filter_by_user(request, fieldsets)
        return fieldsets

    def _filter_by_mode(self, mode: PageMode, fieldsets):  # type: ignore[no-untyped-def]
        if mode is PageMode.VIEW:
            if self.edit_only_fields:
                return filter_fieldsets(fieldsets, lambda f: f in self.edit_only_fields)
            return fieldsets
        # EDIT / ADD: hide read-only-style fields
        ro: Iterable[str] = self.view_only_fields
        return filter_fieldsets(fieldsets, lambda f: is_display_only(f, ro))

    def _filter_by_user(self, request: HttpRequest, fieldsets):  # type: ignore[no-untyped-def]
        if request.user.is_superuser:
            return fieldsets
        return filter_fieldsets(fieldsets, lambda f: f in self.superuser_only_fields)

    # ---- list_display superuser filtering -----------------------------

    def get_list_display(self, request: HttpRequest):  # type: ignore[no-untyped-def]
        list_display = super().get_list_display(request)
        if request.user.is_superuser:
            return list_display
        return tuple(x for x in list_display if x not in self.superuser_only_fields)

    # ---- delete-without-confirm action --------------------------------

    def get_actions(self, request: HttpRequest):  # type: ignore[no-untyped-def]
        actions = super().get_actions(request)
        if self.skip_delete_confirm:
            actions.pop("delete_selected", None)
            actions["delete_without_confirm"] = self.get_action(delete_without_confirm)
        return actions

    # ---- tabbed inlines flag -----------------------------------------

    def get_inline_instances(self, request: HttpRequest, obj: Any = None):  # type: ignore[no-untyped-def]
        request.is_tabbed_admin_extended = self.tabbed_inlines  # type: ignore[attr-defined]
        return super().get_inline_instances(request, obj)
```

Note: `request.is_tabbed_admin_extended` is set as an attribute for the template to read. This is a narrow, namespaced flag — different from the v5 `request.page_type` issue because we no longer rely on it for control flow, only for template rendering.

- [ ] **Step 2: Update core/__init__.py**

```python
"""Core subsystem: ExtendedAdminModel, page mode, field visibility."""
from .model_admin import ExtendedAdminModel
from .page_mode import PageMode, current_page_mode, get_page_mode, page_mode_scope

__all__ = [
    "ExtendedAdminModel",
    "PageMode",
    "current_page_mode",
    "get_page_mode",
    "page_mode_scope",
]
```

- [ ] **Step 3: Run tests**

```bash
pytest admin_extended/tests/test_core_model_admin.py -v
```

Expected: 4 passed.

### Task 5.4: Commit Phase 5

```bash
git add admin_extended/core admin_extended/tests/test_core_model_admin.py
git commit -m "feat(core): ExtendedAdminModel composes page_mode + display + field filters"
```

---

## Phase 6: object_tools/ subsystem

`@object_tool` decorator returning a frozen dataclass + dispatch mixin + permission check (H2).

### Task 6.1: Test the decorator

**Files:**
- Create: `admin_extended/tests/test_object_tools.py`

- [ ] **Step 1: Write decorator tests**

```python
"""Tests for the object_tools subsystem."""
from __future__ import annotations

import pytest

from admin_extended.object_tools import ObjectToolMixin, ObjectToolSpec, object_tool


def test_decorator_attaches_spec_with_defaults():
    @object_tool(label="Recompute")
    def recompute(self, request, object_id):
        return "ok"

    spec: ObjectToolSpec = recompute.object_tool  # type: ignore[attr-defined]
    assert spec.label == "Recompute"
    assert spec.name == "recompute"
    assert spec.icon is None
    assert spec.method == "GET"
    assert spec.post_param is None
    assert spec.require_permission == "change"


def test_decorator_accepts_all_options():
    @object_tool(
        label="Export",
        icon="fas fa-download",
        method="POST",
        post_param="reason",
        require_permission="view",
        name="custom_name",
    )
    def export(self, request):
        return "ok"

    spec = export.object_tool  # type: ignore[attr-defined]
    assert spec.name == "custom_name"
    assert spec.icon == "fas fa-download"
    assert spec.method == "POST"
    assert spec.post_param == "reason"
    assert spec.require_permission == "view"


def test_decorator_rejects_invalid_method():
    with pytest.raises(ValueError, match="method"):
        @object_tool(label="Bad", method="DELETE")  # type: ignore[arg-type]
        def bad(self, request):
            ...


def test_decorator_rejects_invalid_permission():
    with pytest.raises(ValueError, match="require_permission"):
        @object_tool(label="Bad", require_permission="superpower")  # type: ignore[arg-type]
        def bad(self, request):
            ...
```

- [ ] **Step 2: Run to verify it fails**

```bash
pytest admin_extended/tests/test_object_tools.py -v
```

Expected: ModuleNotFoundError.

### Task 6.2: Implement decorator + spec

**Files:**
- Create: `admin_extended/object_tools/__init__.py`
- Create: `admin_extended/object_tools/decorator.py`

- [ ] **Step 1: Write decorator.py**

```python
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
    """Mark a ModelAdmin method as an object tool.

    The decorator attaches an ``ObjectToolSpec`` to the function as the
    ``object_tool`` attribute; ObjectToolMixin discovers it via that attribute.
    """
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
```

- [ ] **Step 2: Write minimal __init__.py**

```python
"""Object tools subsystem — custom action buttons on change form / list."""
from .decorator import ObjectToolSpec, object_tool

__all__ = ["ObjectToolMixin", "ObjectToolSpec", "object_tool"]


def __getattr__(name: str):
    if name == "ObjectToolMixin":
        from .mixin import ObjectToolMixin
        return ObjectToolMixin
    raise AttributeError(name)
```

(Lazy import avoids importing `mixin.py` before it exists; we add it in Task 6.4.)

- [ ] **Step 3: Run decorator tests**

```bash
pytest admin_extended/tests/test_object_tools.py::test_decorator_attaches_spec_with_defaults admin_extended/tests/test_object_tools.py::test_decorator_accepts_all_options admin_extended/tests/test_object_tools.py::test_decorator_rejects_invalid_method admin_extended/tests/test_object_tools.py::test_decorator_rejects_invalid_permission -v
```

Expected: 4 passed.

### Task 6.3: Test the mixin dispatch + permission check

**Files:**
- Modify: `admin_extended/tests/test_object_tools.py`

- [ ] **Step 1: Append mixin tests**

```python
# ----- mixin dispatch tests -----

from django.contrib import admin
from django.http import HttpResponse
from django.urls import reverse

from admin_extended.core import ExtendedAdminModel
from admin_extended.tests.example_project.sample_app.models import Product


class _ProductAdmin(ExtendedAdminModel):
    change_form_tools = ("recompute",)
    change_list_tools = ("export",)

    @object_tool(label="Recompute", icon="fas fa-sync")
    def recompute(self, request, object_id):
        return HttpResponse(f"recomputed {object_id}")

    @object_tool(label="Export CSV", method="POST", post_param="reason", require_permission="view")
    def export(self, request):
        return HttpResponse("exported")


def _register(model, admin_cls):
    if model in admin.site._registry:
        admin.site.unregister(model)
    admin.site.register(model, admin_cls)


def test_change_form_object_tool_dispatch(admin_client, db):
    _register(Product, _ProductAdmin)
    product = Product.objects.create(name="p", price=10)

    url = reverse("admin:sample_app_product_change_form_object_tool", args=[product.pk, "recompute"])
    response = admin_client.get(url)
    assert response.status_code == 200
    assert response.content == f"recomputed {product.pk}".encode()


def test_change_list_object_tool_dispatch(admin_client, db):
    _register(Product, _ProductAdmin)
    url = reverse("admin:sample_app_product_change_list_object_tool", args=["export"])
    response = admin_client.post(url, data={"reason": "test"})
    assert response.status_code == 200
    assert response.content == b"exported"


def test_change_form_tool_denied_without_permission(client, user, db):
    # `user` is staff but has no Product.change permission
    _register(Product, _ProductAdmin)
    client.force_login(user)
    product = Product.objects.create(name="p", price=10)
    url = reverse("admin:sample_app_product_change_form_object_tool", args=[product.pk, "recompute"])
    response = client.get(url)
    assert response.status_code == 403
```

- [ ] **Step 2: Run to verify it fails**

```bash
pytest admin_extended/tests/test_object_tools.py -v
```

Expected: 4 pass, 3 fail (missing mixin / URL not registered).

### Task 6.4: Implement mixin + views

**Files:**
- Create: `admin_extended/object_tools/views.py`
- Create: `admin_extended/object_tools/mixin.py`

- [ ] **Step 1: Write views.py**

```python
"""View helpers shared by ObjectToolMixin."""
from __future__ import annotations

from typing import Any

from django.core.exceptions import PermissionDenied
from django.http import HttpRequest, HttpResponse

from .decorator import ObjectToolSpec


def check_permission(spec: ObjectToolSpec, model_admin: Any, request: HttpRequest, obj: Any = None) -> None:
    if spec.require_permission is None:
        return
    if spec.require_permission == "view":
        if not model_admin.has_view_permission(request, obj):
            raise PermissionDenied
    elif spec.require_permission == "change":
        if not model_admin.has_change_permission(request, obj):
            raise PermissionDenied


def invoke(spec: ObjectToolSpec, model_admin: Any, request: HttpRequest, *args: Any) -> HttpResponse:
    return spec.func(model_admin, request, *args)
```

- [ ] **Step 2: Write mixin.py**

```python
"""ObjectToolMixin — adds change-form and change-list action buttons.

Discovers tools via the ``change_form_tools`` and ``change_list_tools`` class
attributes (lists of method names). Each method must be decorated with
``@object_tool``.
"""
from __future__ import annotations

from typing import Any

from django.urls import path, reverse

from .decorator import ObjectToolSpec
from .views import check_permission, invoke


class ObjectToolMixin:
    change_form_tools: tuple[str, ...] = ()
    change_list_tools: tuple[str, ...] = ()

    # ---- URL registration ---------------------------------------------

    def get_urls(self):  # type: ignore[no-untyped-def]
        urls = super().get_urls()  # type: ignore[misc]
        base = f"{self.model._meta.app_label}_{self.model._meta.model_name}"  # type: ignore[attr-defined]
        custom = [
            path(
                "<path:object_id>/object-tools/<str:name>",
                self.admin_site.admin_view(self._change_form_object_tool_view),  # type: ignore[attr-defined]
                name=f"{base}_change_form_object_tool",
            ),
            path(
                "object-tools/<str:name>",
                self.admin_site.admin_view(self._change_list_object_tool_view),  # type: ignore[attr-defined]
                name=f"{base}_change_list_object_tool",
            ),
        ]
        return custom + urls

    # ---- spec lookup --------------------------------------------------

    def _resolve_specs(self, attr_names: tuple[str, ...]) -> dict[str, ObjectToolSpec]:
        out: dict[str, ObjectToolSpec] = {}
        for attr_name in attr_names:
            method = getattr(self, attr_name)
            spec: ObjectToolSpec | None = getattr(method, "object_tool", None)
            if spec is None:
                raise ValueError(
                    f"{type(self).__name__}.{attr_name} is referenced in tools but is not decorated with @object_tool"
                )
            out[spec.name] = spec
        return out

    def _change_form_specs(self) -> dict[str, ObjectToolSpec]:
        return self._resolve_specs(self.change_form_tools)

    def _change_list_specs(self) -> dict[str, ObjectToolSpec]:
        return self._resolve_specs(self.change_list_tools)

    # ---- dispatchers --------------------------------------------------

    def _change_form_object_tool_view(self, request, object_id, name):  # type: ignore[no-untyped-def]
        spec = self._change_form_specs()[name]
        obj = self.get_object(request, object_id)  # type: ignore[attr-defined]
        check_permission(spec, self, request, obj)
        return invoke(spec, self, request, object_id)

    def _change_list_object_tool_view(self, request, name):  # type: ignore[no-untyped-def]
        spec = self._change_list_specs()[name]
        check_permission(spec, self, request)
        return invoke(spec, self, request)

    # ---- template context ---------------------------------------------

    def _render_change_form_tools(self, request, object_id):  # type: ignore[no-untyped-def]
        base = f"{self.model._meta.app_label}_{self.model._meta.model_name}"  # type: ignore[attr-defined]
        in_object_tools: list[dict[str, Any]] = []
        in_submit_row: list[dict[str, Any]] = []
        for name, spec in self._change_form_specs().items():
            entry = {
                "icon": spec.icon,
                "label": spec.label,
                "url": reverse(f"admin:{base}_change_form_object_tool", args=[object_id, name]),
            }
            if spec.method == "GET":
                in_object_tools.append(entry)
            else:
                entry["post_param"] = spec.post_param
                in_submit_row.append(entry)
        return in_object_tools, in_submit_row

    def _render_change_list_tools(self, request):  # type: ignore[no-untyped-def]
        base = f"{self.model._meta.app_label}_{self.model._meta.model_name}"  # type: ignore[attr-defined]
        return [
            {
                "icon": spec.icon,
                "label": spec.label,
                "url": reverse(f"admin:{base}_change_list_object_tool", args=[name]),
            }
            for name, spec in self._change_list_specs().items()
        ]

    # ---- changeform_view / changelist_view -----------------------------

    def changeform_view(self, request, object_id=None, form_url="", extra_context=None):  # type: ignore[no-untyped-def]
        extra_context = dict(extra_context or {})
        if object_id is not None:
            object_tools, submit_row = self._render_change_form_tools(request, object_id)
            extra_context["admin_extended_object_tools"] = object_tools
            extra_context["admin_extended_submit_row_tools"] = submit_row
        return super().changeform_view(request, object_id, form_url, extra_context)  # type: ignore[misc]

    def changelist_view(self, request, extra_context=None):  # type: ignore[no-untyped-def]
        extra_context = dict(extra_context or {})
        extra_context["admin_extended_changelist_tools"] = self._render_change_list_tools(request)
        return super().changelist_view(request, extra_context)  # type: ignore[misc]
```

- [ ] **Step 3: Wire mixin into ExtendedAdminModel**

Edit `admin_extended/core/model_admin.py` — change the class declaration to include `ObjectToolMixin`:

```python
from ..object_tools.mixin import ObjectToolMixin
# ...
class ExtendedAdminModel(ObjectToolMixin, DisplayLinkAdapter, admin.ModelAdmin):
```

- [ ] **Step 4: Run mixin tests**

```bash
pytest admin_extended/tests/test_object_tools.py -v
```

Expected: 7 passed.

### Task 6.5: Add object-tools templates

**Files:**
- Create: `admin_extended/templates/admin/admin_extended/object_tools/change_form_object_tools.html`
- Create: `admin_extended/templates/admin/admin_extended/object_tools/change_form_submit_row.html`

- [ ] **Step 1: Create directories**

```bash
mkdir -p admin_extended/templates/admin/admin_extended/object_tools
```

- [ ] **Step 2: Write change_form_object_tools.html**

```html
{% load i18n %}
{% for tool in admin_extended_object_tools %}
<li>
  <a href="{{ tool.url }}" class="historylink">
    {% if tool.icon %}<i class="{{ tool.icon }}"></i>{% endif %}
    {{ tool.label }}
  </a>
</li>
{% endfor %}
```

- [ ] **Step 3: Write change_form_submit_row.html**

```html
{% load i18n %}
{% for tool in admin_extended_submit_row_tools %}
<button type="submit" formaction="{{ tool.url }}" name="{{ tool.post_param|default:'' }}" class="default">
  {% if tool.icon %}<i class="{{ tool.icon }}"></i>{% endif %}
  {{ tool.label }}
</button>
{% endfor %}
```

These templates are included by the Phase 11 `change_form.html` / `change_list.html` overrides.

### Task 6.6: Commit Phase 6

```bash
git add admin_extended/object_tools admin_extended/templates admin_extended/tests/test_object_tools.py admin_extended/core/model_admin.py
git commit -m "feat(object_tools): dataclass spec, permission check, dispatcher, templates"
```

---

## Phase 7: autoregister/ subsystem

`DefaultModelAdmin` + `auto_register()` with canonical ignore format.

### Task 7.1: Test DefaultModelAdmin

**Files:**
- Create: `admin_extended/tests/test_autoregister.py`

- [ ] **Step 1: Write tests**

```python
"""Tests for autoregister subsystem."""
from __future__ import annotations

from django.contrib import admin
from django.db import models

from admin_extended.autoregister import DefaultModelAdmin, auto_register
from admin_extended.tests.example_project.sample_app.models import Order, Product


def test_default_list_display_excludes_text_and_json_fields():
    site = admin.AdminSite(name="auto1")
    site.register(Product, DefaultModelAdmin)
    ma = site._registry[Product]

    # 'notes' is TextField -> excluded; 'status' has choices -> included
    assert "name" in ma.list_display
    assert "price" in ma.list_display
    assert "status" in ma.list_display
    assert "notes" not in ma.list_display


def test_default_list_filter_picks_choice_fields():
    site = admin.AdminSite(name="auto2")
    site.register(Product, DefaultModelAdmin)
    ma = site._registry[Product]
    assert tuple(ma.list_filter) == ("status",)


def test_default_select_related_for_fks():
    from django.test import RequestFactory

    site = admin.AdminSite(name="auto3")
    site.register(Order, DefaultModelAdmin)
    ma = site._registry[Order]
    request = RequestFactory().get("/")
    qs = ma.get_queryset(request)
    assert set(qs.query.select_related) >= {"customer", "product"}


def test_auto_register_skips_django_models():
    site = admin.AdminSite(name="auto4")
    auto_register(default_admin=DefaultModelAdmin, ignore=[], site=site)
    registered_modules = {model.__module__ for model in site._registry}
    assert not any(m.startswith("django.") for m in registered_modules)


def test_auto_register_respects_ignore_in_canonical_app_dot_model_format():
    site = admin.AdminSite(name="auto5")
    auto_register(default_admin=DefaultModelAdmin, ignore=["sample_app.Product"], site=site)
    assert Product not in site._registry
    # Other sample_app models still registered
    assert Order in site._registry
```

- [ ] **Step 2: Run to verify it fails**

```bash
pytest admin_extended/tests/test_autoregister.py -v
```

Expected: ModuleNotFoundError.

### Task 7.2: Implement autoregister/

**Files:**
- Create: `admin_extended/autoregister/__init__.py`
- Create: `admin_extended/autoregister/default_admin.py`
- Create: `admin_extended/autoregister/registry.py`

- [ ] **Step 1: Write default_admin.py**

```python
"""DefaultModelAdmin — auto-populates list_display, list_filter, select_related."""
from __future__ import annotations

from typing import Any

from django.db.models import JSONField, TextField

from ..core import ExtendedAdminModel

_END_OF_LIST_DISPLAY = ("created_at", "created", "modified_at", "modified")


class DefaultModelAdmin(ExtendedAdminModel):
    """ModelAdmin that picks sensible defaults from the model schema."""

    list_display_ignore_field_types: tuple[type, ...] = (TextField, JSONField)
    list_display_ignore_field_names: tuple[str, ...] = ()

    def __init__(self, model, admin_site):  # type: ignore[no-untyped-def]
        if self.list_display == ("__str__",):
            self.list_display = self._build_list_display(model)
        if not self.list_filter:
            self.list_filter = tuple(f.name for f in model._meta.fields if f.choices)
        super().__init__(model, admin_site)

    def _build_list_display(self, model: Any) -> tuple[str, ...]:
        cols: list[str] = ["__str__"]
        for field in model._meta.fields:
            if self._ignore(field):
                continue
            cols.append(field.name)
        # Move timestamps to the end
        for name in _END_OF_LIST_DISPLAY:
            if name in cols:
                cols.append(cols.pop(cols.index(name)))
        return tuple(cols)

    def _ignore(self, field: Any) -> bool:
        if field.name == "id":
            return True
        if isinstance(field, self.list_display_ignore_field_types):
            return True
        return field.name in self.list_display_ignore_field_names

    def get_queryset(self, request):  # type: ignore[no-untyped-def]
        qs = super().get_queryset(request)
        related = tuple(f.name for f in self.model._meta.fields if f.is_relation)  # type: ignore[attr-defined]
        if related:
            qs = qs.select_related(*related)
        return qs
```

- [ ] **Step 2: Write registry.py**

```python
"""auto_register — register every non-Django model with a default admin."""
from __future__ import annotations

from collections.abc import Iterable

from django.apps import apps
from django.contrib import admin

from .default_admin import DefaultModelAdmin


def auto_register(
    *,
    default_admin: type[admin.ModelAdmin] = DefaultModelAdmin,
    ignore: Iterable[str] | None = None,
    site: admin.AdminSite | None = None,
) -> None:
    """Register every model from non-Django apps that is not already registered.

    Args:
        default_admin: ModelAdmin class to register each model with.
        ignore: identifiers ``'app_label.ModelName'`` to skip.
        site: AdminSite to register into (defaults to ``admin.site``).
    """
    ignore_set = {x.lower() for x in (ignore or ())}
    target_site = site or admin.site

    for model in apps.get_models():
        identity = f"{model._meta.app_label}.{model.__name__}".lower()
        if model.__module__.startswith("django."):
            continue
        if identity in ignore_set:
            continue
        try:
            target_site.register(model, default_admin)
        except admin.sites.AlreadyRegistered:
            continue
```

- [ ] **Step 3: Write __init__.py**

```python
"""Autoregister subsystem."""
from .default_admin import DefaultModelAdmin
from .registry import auto_register

__all__ = ["DefaultModelAdmin", "auto_register"]
```

- [ ] **Step 4: Run tests**

```bash
pytest admin_extended/tests/test_autoregister.py -v
```

Expected: 5 passed.

### Task 7.3: Commit Phase 7

```bash
git add admin_extended/autoregister admin_extended/tests/test_autoregister.py
git commit -m "feat(autoregister): DefaultModelAdmin + canonical app.Model ignore format"
```

---

## Phase 8: custom_pages/

`CustomTableAdminPage` + `TableData` with B1 fix.

### Task 8.1: Test TableData mutable bug regression

**Files:**
- Create: `admin_extended/tests/test_custom_pages.py`

- [ ] **Step 1: Write tests**

```python
"""Tests for custom_pages subsystem (B1 regression)."""
from __future__ import annotations

from admin_extended.custom_pages import TableData


def test_table_data_instances_do_not_share_state_b1_regression():
    """v5 had class-level mutable lists; v6 must use default_factory."""
    a = TableData(header="A")
    b = TableData(header="B")
    a.add_row(["x"])
    assert a.rows == [["x"]]
    assert b.rows == []  # Would fail in v5


def test_table_data_titles_independent():
    a = TableData(header="A", titles=["Col1"])
    b = TableData(header="B")
    assert a.titles == ["Col1"]
    assert b.titles == []


def test_add_row_appends_single_row():
    t = TableData(header="X")
    t.add_row([1, 2, 3])
    t.add_row([4, 5, 6])
    assert t.rows == [[1, 2, 3], [4, 5, 6]]
```

- [ ] **Step 2: Run to verify it fails**

```bash
pytest admin_extended/tests/test_custom_pages.py -v
```

Expected: ModuleNotFoundError.

### Task 8.2: Implement custom_pages/

**Files:**
- Create: `admin_extended/custom_pages/__init__.py`
- Create: `admin_extended/custom_pages/table_page.py`

- [ ] **Step 1: Write table_page.py**

```python
"""Custom table admin page that replaces the changelist with bespoke HTML."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from django.contrib import admin
from django.http import HttpRequest, HttpResponse
from django.shortcuts import render
from django.urls import path


@dataclass
class TableData:
    header: str
    titles: list[str] = field(default_factory=list)
    rows: list[list[Any]] = field(default_factory=list)

    def add_row(self, row: list[Any]) -> None:
        self.rows.append(row)


class CustomTableAdminPage(admin.ModelAdmin):
    """ModelAdmin whose changelist is a custom table.

    Override ``get_table_data`` to return a list of ``TableData`` instances.
    """

    model: type | None = None

    def get_urls(self):  # type: ignore[no-untyped-def]
        if self.model is None:
            raise RuntimeError("CustomTableAdminPage subclasses must set 'model'")
        view_name = f"{self.model._meta.app_label}_{self.model._meta.model_name}_changelist"  # type: ignore[union-attr]
        return [path("", self._custom_view, name=view_name)]

    def get_table_data(self) -> list[TableData]:
        raise NotImplementedError

    def _custom_view(self, request: HttpRequest) -> HttpResponse:
        context = {
            **admin.site.each_context(request),
            "tables": self.get_table_data(),
        }
        return render(request, "admin/admin_extended/custom_pages/custom_table_page.html", context)
```

- [ ] **Step 2: Write __init__.py**

```python
"""Custom pages subsystem."""
from .table_page import CustomTableAdminPage, TableData

__all__ = ["CustomTableAdminPage", "TableData"]
```

- [ ] **Step 3: Create the template**

```bash
mkdir -p admin_extended/templates/admin/admin_extended/custom_pages
```

Write `admin_extended/templates/admin/admin_extended/custom_pages/custom_table_page.html`:

```html
{% extends "admin/base_site.html" %}
{% block content %}
{% for table in tables %}
  <h2>{{ table.header }}</h2>
  <table>
    <thead>
      <tr>{% for title in table.titles %}<th>{{ title }}</th>{% endfor %}</tr>
    </thead>
    <tbody>
      {% for row in table.rows %}<tr>{% for cell in row %}<td>{{ cell }}</td>{% endfor %}</tr>{% endfor %}
    </tbody>
  </table>
{% endfor %}
{% endblock %}
```

- [ ] **Step 4: Run tests**

```bash
pytest admin_extended/tests/test_custom_pages.py -v
```

Expected: 3 passed.

### Task 8.3: Commit Phase 8

```bash
git add admin_extended/custom_pages admin_extended/templates/admin/admin_extended/custom_pages admin_extended/tests/test_custom_pages.py
git commit -m "feat(custom_pages): TableData fix shared mutable state (B1)"
```

---

## Phase 9: bookmarks/ sub-app

Standalone Django sub-app: `Bookmark` model + admin (no `@csrf_exempt`) + templatetag side-effects.

### Task 9.1: Scaffold the sub-app

**Files:**
- Create: `admin_extended/bookmarks/__init__.py`
- Create: `admin_extended/bookmarks/apps.py`
- Create: `admin_extended/bookmarks/models.py`
- Create: `admin_extended/bookmarks/migrations/__init__.py`
- Create: `admin_extended/bookmarks/migrations/0001_initial.py`

- [ ] **Step 1: Create dirs**

```bash
mkdir -p admin_extended/bookmarks/migrations
touch admin_extended/bookmarks/__init__.py
touch admin_extended/bookmarks/migrations/__init__.py
```

- [ ] **Step 2: Write apps.py**

```python
from django.apps import AppConfig


class BookmarksConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "admin_extended.bookmarks"
    label = "admin_extended_bookmarks"
    verbose_name = "Bookmarks"
```

- [ ] **Step 3: Write models.py**

```python
from __future__ import annotations

from django.db import models


class Bookmark(models.Model):
    name = models.CharField(max_length=45)
    url = models.CharField(max_length=1000)
    is_active = models.BooleanField(default=True)
    order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ("order", "id")

    def __str__(self) -> str:
        return self.name
```

- [ ] **Step 4: Write migration 0001_initial.py**

```python
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True
    dependencies = []
    operations = [
        migrations.CreateModel(
            name="Bookmark",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                ("name", models.CharField(max_length=45)),
                ("url", models.CharField(max_length=1000)),
                ("is_active", models.BooleanField(default=True)),
                ("order", models.PositiveSmallIntegerField(default=0)),
            ],
            options={"ordering": ("order", "id")},
        ),
    ]
```

### Task 9.2: Enable bookmarks in example_project settings

**Files:**
- Modify: `admin_extended/tests/example_project/settings.py`

- [ ] **Step 1: Uncomment bookmarks in INSTALLED_APPS**

Change the line:

```python
    # "admin_extended.bookmarks",   # enabled in Phase 9
```

to:

```python
    "admin_extended.bookmarks",
```

### Task 9.3: Test bookmark admin

**Files:**
- Create: `admin_extended/tests/test_bookmarks.py`

- [ ] **Step 1: Write tests**

```python
"""Tests for bookmarks sub-app."""
from __future__ import annotations

from django.urls import reverse

from admin_extended.bookmarks.models import Bookmark


def test_bookmark_str_returns_name(db):
    b = Bookmark.objects.create(name="Docs", url="https://example.com")
    assert str(b) == "Docs"


def test_admin_changelist_renders(admin_client, db):
    Bookmark.objects.create(name="A", url="https://a/")
    url = reverse("admin:admin_extended_bookmarks_bookmark_changelist")
    response = admin_client.get(url)
    assert response.status_code == 200


def test_admin_create_via_changeform(admin_client, db):
    url = reverse("admin:admin_extended_bookmarks_bookmark_add")
    response = admin_client.post(
        url,
        data={"name": "New", "url": "https://x/", "is_active": "on", "order": "0", "_save": "Save"},
    )
    assert response.status_code in (200, 302)
    assert Bookmark.objects.filter(name="New").exists()
```

- [ ] **Step 2: Run to verify it fails**

```bash
pytest admin_extended/tests/test_bookmarks.py -v
```

Expected: missing admin registration → some pass, changelist URL not reverse-able.

### Task 9.4: Implement BookmarkAdmin

**Files:**
- Create: `admin_extended/bookmarks/admin.py`

- [ ] **Step 1: Write admin.py**

```python
"""Bookmark admin — plain ModelAdmin, no custom endpoints."""
from __future__ import annotations

from django.contrib import admin

from .models import Bookmark


@admin.register(Bookmark)
class BookmarkAdmin(admin.ModelAdmin):
    list_display = ("name", "url", "is_active", "order")
    list_filter = ("is_active",)
    list_editable = ("is_active", "order")
    search_fields = ("name", "url")
```

- [ ] **Step 2: Run tests**

```bash
pytest admin_extended/tests/test_bookmarks.py -v
```

Expected: 3 passed.

### Task 9.5: Commit Phase 9

```bash
git add admin_extended/bookmarks admin_extended/tests/test_bookmarks.py admin_extended/tests/example_project/settings.py
git commit -m "feat(bookmarks): split into sub-app, drop csrf_exempt POST endpoint (B2)"
```

---

## Phase 10: charts/ sub-app

Largest phase. Splits the v5 monolithic chart code into model + service + form + views.

### Task 10.1: Scaffold the sub-app

**Files:**
- Create: `admin_extended/charts/__init__.py`
- Create: `admin_extended/charts/apps.py`
- Create: `admin_extended/charts/migrations/__init__.py`

- [ ] **Step 1: Create dirs**

```bash
mkdir -p admin_extended/charts/migrations
mkdir -p admin_extended/charts/templates/admin/admin_extended/charts
touch admin_extended/charts/__init__.py
touch admin_extended/charts/migrations/__init__.py
```

- [ ] **Step 2: Write apps.py**

```python
from django.apps import AppConfig


class ChartsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "admin_extended.charts"
    label = "admin_extended_charts"
    verbose_name = "Admin Charts"
```

### Task 10.2: Define TimeSeriesChart model

**Files:**
- Create: `admin_extended/charts/models.py`
- Create: `admin_extended/charts/migrations/0001_initial.py`

- [ ] **Step 1: Write models.py**

```python
"""TimeSeriesChart model + enums + Scale -> Trunc mapping (single source of truth)."""
from __future__ import annotations

from typing import Any

from django.apps import apps as django_apps
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models.functions import TruncDay, TruncHour, TruncMonth, TruncWeek


class Aggregate(models.TextChoices):
    COUNT = "COUNT", "COUNT"
    SUM = "SUM", "SUM"
    AVG = "AVG", "AVG"
    MIN = "MIN", "MIN"
    MAX = "MAX", "MAX"


class TimeRange(models.IntegerChoices):
    LAST_7_DAY = 7, "Last 7 days"
    LAST_30_DAY = 30, "Last 30 days"
    LAST_YEAR = 365, "Last 1 year"
    ALL_TIME = 0, "All time"


class Scale(models.TextChoices):
    HOUR = "HOUR", "Hour"
    DAY = "DAY", "Day"
    WEEK = "WEEK", "Week"
    MONTH = "MONTH", "Month"


class ChartType(models.TextChoices):
    BAR = "BAR", "Bar"
    LINE = "LINE", "Line"


_TRUNC_FOR_SCALE: dict[str, type] = {
    Scale.HOUR: TruncHour,
    Scale.DAY: TruncDay,
    Scale.WEEK: TruncWeek,
    Scale.MONTH: TruncMonth,
}


def trunc_for(scale: str) -> type:
    return _TRUNC_FOR_SCALE[scale]


class TimeSeriesChart(models.Model):
    name = models.CharField(max_length=255)
    description = models.CharField(max_length=1000, null=True, blank=True, default=None)
    chart_type = models.CharField(max_length=55, choices=ChartType.choices, default=ChartType.BAR)
    stacked = models.BooleanField(default=False)

    default_time_range = models.IntegerField(choices=TimeRange.choices, default=TimeRange.LAST_30_DAY)
    default_scale = models.CharField(max_length=45, choices=Scale.choices, default=Scale.DAY)

    target_app_label = models.CharField(max_length=255)
    target_model_name = models.CharField(max_length=255)
    time_field = models.CharField(max_length=255)
    aggregate = models.CharField(max_length=45, choices=Aggregate.choices)
    aggregate_field = models.CharField(max_length=255, default="*")
    aggregate_label = models.CharField(max_length=255)

    split_field = models.CharField(max_length=255, null=True, blank=True, default=None)
    filter_field = models.CharField(max_length=255, null=True, blank=True, default=None)
    filters = models.CharField(
        max_length=1000, null=True, blank=True, default=None,
        help_text="Filters for query. Example: status=1&cate=3",
    )

    max_points = models.PositiveIntegerField(default=1000)
    cache_seconds = models.PositiveIntegerField(default=0, help_text="0 = no cache")

    def __str__(self) -> str:
        return self.name

    # ---- helpers --------------------------------------------------------

    def get_target_model(self) -> type[models.Model]:
        return django_apps.get_model(app_label=self.target_app_label, model_name=self.target_model_name)

    def get_aggregate(self) -> Any:
        return {
            Aggregate.COUNT: models.Count,
            Aggregate.SUM: models.Sum,
            Aggregate.AVG: models.Avg,
            Aggregate.MIN: models.Min,
            Aggregate.MAX: models.Max,
        }[self.aggregate](self.aggregate_field)

    # ---- validation ----------------------------------------------------

    def clean(self) -> None:
        try:
            target = self.get_target_model()
        except LookupError as err:
            raise ValidationError({"target_model_name": "Target model does not exist"}) from err

        field_names = {f.name for f in target._meta.fields}

        if self.time_field not in field_names:
            raise ValidationError({"time_field": f"'{self.time_field}' is not a field of {target.__name__}"})

        if self.aggregate != Aggregate.COUNT and self.aggregate_field == "*":
            raise ValidationError({"aggregate_field": f"{self.aggregate} requires a specific field"})

        if self.aggregate_field != "*" and self.aggregate_field not in field_names:
            raise ValidationError({"aggregate_field": f"'{self.aggregate_field}' is not a field of {target.__name__}"})

        if self.split_field and self.split_field not in field_names:
            raise ValidationError({"split_field": f"'{self.split_field}' is not a field of {target.__name__}"})

        if self.filter_field and self.filter_field not in field_names:
            raise ValidationError({"filter_field": f"'{self.filter_field}' is not a field of {target.__name__}"})

        if self.filters:
            try:
                from urllib.parse import parse_qsl
                parse_qsl(self.filters, keep_blank_values=False, strict_parsing=True)
            except ValueError as err:
                raise ValidationError({"filters": "Could not parse as query string"}) from err
```

- [ ] **Step 2: Write migration 0001_initial.py**

```python
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True
    dependencies = []
    operations = [
        migrations.CreateModel(
            name="TimeSeriesChart",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                ("name", models.CharField(max_length=255)),
                ("description", models.CharField(blank=True, default=None, max_length=1000, null=True)),
                (
                    "chart_type",
                    models.CharField(choices=[("BAR", "Bar"), ("LINE", "Line")], default="BAR", max_length=55),
                ),
                ("stacked", models.BooleanField(default=False)),
                (
                    "default_time_range",
                    models.IntegerField(
                        choices=[(7, "Last 7 days"), (30, "Last 30 days"), (365, "Last 1 year"), (0, "All time")],
                        default=30,
                    ),
                ),
                (
                    "default_scale",
                    models.CharField(
                        choices=[("HOUR", "Hour"), ("DAY", "Day"), ("WEEK", "Week"), ("MONTH", "Month")],
                        default="DAY",
                        max_length=45,
                    ),
                ),
                ("target_app_label", models.CharField(max_length=255)),
                ("target_model_name", models.CharField(max_length=255)),
                ("time_field", models.CharField(max_length=255)),
                (
                    "aggregate",
                    models.CharField(
                        choices=[
                            ("COUNT", "COUNT"), ("SUM", "SUM"), ("AVG", "AVG"), ("MIN", "MIN"), ("MAX", "MAX")
                        ],
                        max_length=45,
                    ),
                ),
                ("aggregate_field", models.CharField(default="*", max_length=255)),
                ("aggregate_label", models.CharField(max_length=255)),
                ("split_field", models.CharField(blank=True, default=None, max_length=255, null=True)),
                ("filter_field", models.CharField(blank=True, default=None, max_length=255, null=True)),
                (
                    "filters",
                    models.CharField(
                        blank=True, default=None, help_text="Filters for query. Example: status=1&cate=3",
                        max_length=1000, null=True,
                    ),
                ),
                ("max_points", models.PositiveIntegerField(default=1000)),
                (
                    "cache_seconds",
                    models.PositiveIntegerField(default=0, help_text="0 = no cache"),
                ),
            ],
        ),
    ]
```

### Task 10.3: Enable charts in example_project settings

**Files:**
- Modify: `admin_extended/tests/example_project/settings.py`

- [ ] **Step 1: Uncomment charts in INSTALLED_APPS**

Change:

```python
    # "admin_extended.charts",      # enabled in Phase 10
```

to:

```python
    "admin_extended.charts",
```

### Task 10.4: Test model clean()

**Files:**
- Create: `admin_extended/tests/test_charts_models.py`

- [ ] **Step 1: Write tests**

```python
"""Tests for TimeSeriesChart.clean() validation."""
from __future__ import annotations

import pytest
from django.core.exceptions import ValidationError

from admin_extended.charts.models import Aggregate, TimeSeriesChart


def _make(**kw) -> TimeSeriesChart:
    defaults = dict(
        name="t",
        target_app_label="sample_app",
        target_model_name="Order",
        time_field="created_at",
        aggregate=Aggregate.COUNT,
        aggregate_field="*",
        aggregate_label="orders",
    )
    defaults.update(kw)
    return TimeSeriesChart(**defaults)


def test_clean_accepts_valid_count_chart(db):
    _make().clean()  # no raise


def test_clean_rejects_unknown_model(db):
    with pytest.raises(ValidationError, match="target_model_name"):
        _make(target_model_name="DoesNotExist").clean()


def test_clean_rejects_unknown_time_field(db):
    with pytest.raises(ValidationError, match="time_field"):
        _make(time_field="missing_at").clean()


def test_clean_requires_specific_field_for_sum(db):
    with pytest.raises(ValidationError, match="aggregate_field"):
        _make(aggregate=Aggregate.SUM, aggregate_field="*").clean()


def test_clean_accepts_sum_with_valid_field(db):
    _make(aggregate=Aggregate.SUM, aggregate_field="quantity").clean()


def test_clean_rejects_split_field_not_on_model(db):
    with pytest.raises(ValidationError, match="split_field"):
        _make(split_field="missing").clean()


def test_clean_rejects_malformed_filters(db):
    with pytest.raises(ValidationError, match="filters"):
        _make(filters="not a query string").clean()
```

- [ ] **Step 2: Run**

```bash
pytest admin_extended/tests/test_charts_models.py -v
```

Expected: 7 passed.

### Task 10.5: Test ChartQueryService

**Files:**
- Create: `admin_extended/tests/test_charts_service.py`

- [ ] **Step 1: Write tests**

```python
"""Tests for ChartQueryService — pure query logic."""
from __future__ import annotations

from datetime import timedelta

import pytest
from django.utils import timezone

from admin_extended.charts.models import Aggregate, Scale, TimeRange, TimeSeriesChart
from admin_extended.charts.services import ChartParams, ChartQueryService, ChartResult
from admin_extended.tests.example_project.sample_app.models import Customer, Order, Product


@pytest.fixture
def chart(db) -> TimeSeriesChart:
    return TimeSeriesChart.objects.create(
        name="orders-by-day",
        target_app_label="sample_app",
        target_model_name="Order",
        time_field="created_at",
        aggregate=Aggregate.COUNT,
        aggregate_field="*",
        aggregate_label="orders",
    )


@pytest.fixture
def seeded(db):
    customer = Customer.objects.create(name="C", email="c@c.com")
    product = Product.objects.create(name="P", price=1)
    now = timezone.now()
    for offset in (0, 1, 2):
        for _ in range(2 + offset):
            o = Order.objects.create(customer=customer, product=product, quantity=1)
            Order.objects.filter(pk=o.pk).update(created_at=now - timedelta(days=offset))
    return customer, product


def test_run_returns_chart_result(chart, seeded):
    result = chart  # noqa: F841 — fixture used
    svc = ChartQueryService(chart)
    params = ChartParams(time_range=TimeRange.LAST_7_DAY, scale=Scale.DAY, filter_value=None)
    out = svc.run(params)
    assert isinstance(out, ChartResult)
    assert out.chart_type == chart.chart_type
    assert len(out.labels) >= 1
    assert len(out.datasets) == 1
    assert out.datasets[0].label == "orders"


def test_run_caps_to_max_points(chart, seeded):
    chart.max_points = 1
    chart.save()
    svc = ChartQueryService(chart)
    params = ChartParams(time_range=TimeRange.ALL_TIME, scale=Scale.DAY, filter_value=None)
    out = svc.run(params)
    assert len(out.labels) <= 1
```

- [ ] **Step 2: Run to verify it fails**

```bash
pytest admin_extended/tests/test_charts_service.py -v
```

Expected: ModuleNotFoundError for `admin_extended.charts.services`.

### Task 10.6: Implement ChartQueryService

**Files:**
- Create: `admin_extended/charts/services.py`

- [ ] **Step 1: Write services.py**

```python
"""Pure query layer for TimeSeriesChart — no HTTP, no JSON."""
from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from datetime import timedelta
from typing import Any
from urllib.parse import parse_qsl

from django.core.cache import cache
from django.db.models import F
from django.utils import timezone

from .models import Scale, TimeRange, TimeSeriesChart, trunc_for


@dataclass(frozen=True, slots=True)
class ChartParams:
    time_range: int
    scale: str
    filter_value: str | None = None


@dataclass(frozen=True, slots=True)
class ChartSeries:
    label: str
    data: list[float]


@dataclass(frozen=True, slots=True)
class ChartResult:
    chart_type: str
    stacked: bool
    labels: list[str]
    datasets: list[ChartSeries]


class ChartQueryService:
    def __init__(self, chart: TimeSeriesChart) -> None:
        self.chart = chart

    # ---- filter choices (cached 5min) ---------------------------------

    def filter_choices(self) -> list[tuple[str, str]]:
        chart = self.chart
        if not chart.filter_field:
            return []
        key = f"admin_extended_charts:filter_choices:{chart.pk}"
        cached = cache.get(key)
        if cached is not None:
            return cached
        target = chart.get_target_model()
        values = list(target.objects.values_list(chart.filter_field, flat=True).distinct())
        choices = [(str(v), str(v)) for v in values if v is not None]
        cache.set(key, choices, 300)
        return choices

    # ---- run / run_cached --------------------------------------------

    def run(self, params: ChartParams) -> ChartResult:
        chart = self.chart
        target = chart.get_target_model()
        bucket = trunc_for(params.scale)(chart.time_field)

        filters: dict[str, Any] = dict(parse_qsl(chart.filters or ""))
        if params.filter_value and chart.filter_field:
            filters[chart.filter_field] = params.filter_value
        if params.time_range:
            filters[f"{chart.time_field}__gte"] = timezone.now() - timedelta(days=params.time_range)

        qs = target.objects.filter(**filters).annotate(time=bucket)
        values_kwargs: dict[str, Any] = {}
        if chart.split_field:
            values_kwargs["split"] = F(chart.split_field)
            qs = qs.values("time", **values_kwargs)
        else:
            qs = qs.values("time")
        qs = qs.annotate(total=chart.get_aggregate()).order_by("time")[: chart.max_points]

        rows = list(qs)
        return self._shape(rows, params.scale)

    def run_cached(self, params: ChartParams) -> ChartResult:
        if self.chart.cache_seconds <= 0:
            return self.run(params)
        key = f"admin_extended_charts:result:{self.chart.pk}:{hash(params)}"
        cached = cache.get(key)
        if cached is not None:
            return cached
        result = self.run(params)
        cache.set(key, result, self.chart.cache_seconds)
        return result

    # ---- shaping ------------------------------------------------------

    def _date_format(self, scale: str) -> str:
        return "%Y-%m-%d %H:%M" if scale == Scale.HOUR else "%Y-%m-%d"

    def _shape(self, rows: list[dict[str, Any]], scale: str) -> ChartResult:
        chart = self.chart
        date_fmt = self._date_format(scale)

        if not chart.split_field:
            labels = [row["time"].strftime(date_fmt) for row in rows]
            data = [float(row["total"] or 0) for row in rows]
            datasets = [ChartSeries(label=chart.aggregate_label, data=data)]
        else:
            labels: list[str] = []
            seen: set[str] = set()
            by_split: dict[str, dict[str, float]] = defaultdict(dict)
            for row in rows:
                label = row["time"].strftime(date_fmt)
                if label not in seen:
                    labels.append(label)
                    seen.add(label)
                by_split[row["split"]][label] = float(row["total"] or 0)
            datasets = [
                ChartSeries(label=str(k), data=[by_split[k].get(label, 0.0) for label in labels])
                for k in by_split
            ]

        return ChartResult(
            chart_type=chart.chart_type,
            stacked=chart.stacked,
            labels=labels,
            datasets=datasets,
        )
```

- [ ] **Step 2: Run service tests**

```bash
pytest admin_extended/tests/test_charts_service.py -v
```

Expected: 2 passed.

### Task 10.7: Test + implement form

**Files:**
- Create: `admin_extended/tests/test_charts_form.py`
- Create: `admin_extended/charts/forms.py`

- [ ] **Step 1: Write test**

```python
"""Tests for ChartParamsForm."""
from __future__ import annotations

from admin_extended.charts.forms import ChartParamsForm
from admin_extended.charts.models import Aggregate, Scale, TimeRange, TimeSeriesChart


def _chart(**kw) -> TimeSeriesChart:
    defaults = dict(
        name="t", target_app_label="sample_app", target_model_name="Order",
        time_field="created_at", aggregate=Aggregate.COUNT, aggregate_field="*",
        aggregate_label="orders",
    )
    defaults.update(kw)
    return TimeSeriesChart.objects.create(**defaults)


def test_form_without_filter_field_omits_filter_value(db):
    chart = _chart()
    form = ChartParamsForm({"time_range": "7", "scale": Scale.DAY}, chart=chart)
    assert "filter_value" not in form.fields


def test_form_with_filter_field_offers_choices(db):
    chart = _chart(filter_field="region")
    form = ChartParamsForm({"time_range": "7", "scale": Scale.DAY}, chart=chart)
    assert "filter_value" in form.fields
    assert form.fields["filter_value"].choices[0] == ("", "All")


def test_form_time_range_coerced_to_int(db):
    chart = _chart()
    form = ChartParamsForm({"time_range": "7", "scale": Scale.DAY}, chart=chart)
    assert form.is_valid(), form.errors
    assert form.cleaned_data["time_range"] == 7
    assert form.cleaned_data["time_range"] == TimeRange.LAST_7_DAY


def test_form_rejects_invalid_scale(db):
    chart = _chart()
    form = ChartParamsForm({"time_range": "7", "scale": "DECADE"}, chart=chart)
    assert not form.is_valid()
    assert "scale" in form.errors
```

- [ ] **Step 2: Run to verify it fails**

```bash
pytest admin_extended/tests/test_charts_form.py -v
```

Expected: ModuleNotFoundError.

- [ ] **Step 3: Write forms.py**

```python
"""ChartParamsForm — single form for both metrics and chart views."""
from __future__ import annotations

from django import forms

from .models import Scale, TimeRange, TimeSeriesChart
from .services import ChartQueryService


class ChartParamsForm(forms.Form):
    time_range = forms.TypedChoiceField(choices=TimeRange.choices, coerce=int)
    scale = forms.ChoiceField(choices=Scale.choices)
    filter_value = forms.ChoiceField(required=False)

    def __init__(self, *args, chart: TimeSeriesChart, **kwargs):  # type: ignore[no-untyped-def]
        super().__init__(*args, **kwargs)
        if chart.filter_field:
            choices = ChartQueryService(chart).filter_choices()
            self.fields["filter_value"].choices = [("", "All"), *choices]
            self.fields["filter_value"].label = chart.filter_field.replace("_", " ").title()
        else:
            self.fields.pop("filter_value")
```

- [ ] **Step 4: Run form tests**

```bash
pytest admin_extended/tests/test_charts_form.py -v
```

Expected: 4 passed.

### Task 10.8: Test + implement views

**Files:**
- Create: `admin_extended/tests/test_charts_views.py`
- Create: `admin_extended/charts/views.py`
- Create: `admin_extended/charts/urls.py`

- [ ] **Step 1: Write tests**

```python
"""Tests for chart views."""
from __future__ import annotations

from django.urls import reverse

from admin_extended.charts.models import Aggregate, TimeSeriesChart


def _chart(**kw) -> TimeSeriesChart:
    defaults = dict(
        name="t", target_app_label="sample_app", target_model_name="Order",
        time_field="created_at", aggregate=Aggregate.COUNT, aggregate_field="*",
        aggregate_label="orders",
    )
    defaults.update(kw)
    return TimeSeriesChart.objects.create(**defaults)


def test_metrics_view_returns_json(admin_client, db):
    chart = _chart()
    url = reverse("admin:admin_extended_charts_metrics", args=[chart.pk])
    response = admin_client.get(url)
    assert response.status_code == 200
    data = response.json()
    assert "labels" in data and "datasets" in data


def test_metrics_view_rejects_invalid_scale(admin_client, db):
    chart = _chart()
    url = reverse("admin:admin_extended_charts_metrics", args=[chart.pk])
    response = admin_client.get(url, {"scale": "DECADE"})
    assert response.status_code == 400


def test_metrics_view_requires_staff(client, db):
    chart = _chart()
    url = reverse("admin:admin_extended_charts_metrics", args=[chart.pk])
    response = client.get(url)
    # admin_view redirects to login
    assert response.status_code in (302, 403)


def test_chart_view_renders_html(admin_client, db):
    chart = _chart()
    url = reverse("admin:admin_extended_charts_chart", args=[chart.pk])
    response = admin_client.get(url)
    assert response.status_code == 200
```

- [ ] **Step 2: Run to verify it fails**

```bash
pytest admin_extended/tests/test_charts_views.py -v
```

Expected: ModuleNotFoundError or url-not-found.

- [ ] **Step 3: Write views.py**

```python
"""MetricsView (JSON) and ChartView (HTML) for TimeSeriesChart."""
from __future__ import annotations

from dataclasses import asdict
from typing import Any

from django.contrib import admin
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404
from django.template.response import TemplateResponse
from django.urls import reverse
from django.views.generic import View

from .forms import ChartParamsForm
from .models import TimeSeriesChart
from .services import ChartParams, ChartQueryService


class _BaseChartView(View):
    chart: TimeSeriesChart

    def dispatch(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:  # type: ignore[override]
        self.chart = get_object_or_404(TimeSeriesChart, pk=kwargs["chart_id"])
        return super().dispatch(request, *args, **kwargs)

    def _resolve_params(self, request: HttpRequest) -> ChartParams | HttpResponse:
        data = {
            "time_range": str(self.chart.default_time_range),
            "scale": self.chart.default_scale,
        }
        data.update(request.GET.dict())
        form = ChartParamsForm(data, chart=self.chart)
        if not form.is_valid():
            return JsonResponse({"errors": form.errors}, status=400)
        cd = form.cleaned_data
        return ChartParams(
            time_range=cd["time_range"],
            scale=cd["scale"],
            filter_value=cd.get("filter_value") or None,
        )


class MetricsView(_BaseChartView):
    def get(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        params = self._resolve_params(request)
        if isinstance(params, HttpResponse):
            return params
        result = ChartQueryService(self.chart).run_cached(params)
        payload = {
            "chart_type": result.chart_type,
            "stacked": result.stacked,
            "labels": result.labels,
            "datasets": [asdict(s) for s in result.datasets],
        }
        return JsonResponse(payload)


class ChartView(_BaseChartView):
    def get(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        chart = self.chart
        form = ChartParamsForm(request.GET or None, chart=chart)
        context = {
            **admin.site.each_context(request),
            "chart": chart,
            "chart_title": chart.name,
            "form": form,
            "metrics_url": reverse("admin:admin_extended_charts_metrics", args=[chart.pk]),
        }
        return TemplateResponse(request, "admin/admin_extended/charts/chart.html", context)
```

- [ ] **Step 4: Write urls.py**

```python
"""URL patterns for chart views, mounted by ChartAdmin.get_urls."""
from __future__ import annotations

from django.urls import path

from .views import ChartView, MetricsView

urlpatterns = [
    path("<int:chart_id>/chart/", ChartView.as_view(), name="admin_extended_charts_chart"),
    path("<int:chart_id>/metrics/", MetricsView.as_view(), name="admin_extended_charts_metrics"),
]
```

### Task 10.9: Implement admin.py + template

**Files:**
- Create: `admin_extended/charts/admin.py`
- Create: `admin_extended/charts/templates/admin/admin_extended/charts/chart.html`

- [ ] **Step 1: Write admin.py**

```python
"""TimeSeriesChartAdmin — thin layer that mounts the chart URLs."""
from __future__ import annotations

from django.contrib import admin
from django.urls import reverse

from ..core import ExtendedAdminModel
from ..display import html_link
from .models import TimeSeriesChart


@admin.register(TimeSeriesChart)
class TimeSeriesChartAdmin(ExtendedAdminModel):
    list_display = ("name", "chart_type", "target_app_label", "target_model_name", "chart_link")
    list_display_links = ("name",)
    search_fields = ("name",)

    fieldsets = (
        (None, {"fields": ("name", "description", ("chart_type", "stacked"))}),
        ("Target model", {"fields": (
            ("target_app_label", "target_model_name", "time_field"),
            ("aggregate", "aggregate_field", "aggregate_label"),
            ("split_field", "filter_field", "filters"),
        )}),
        ("Time options", {"fields": ("default_time_range", "default_scale")}),
        ("Performance", {"fields": (("max_points", "cache_seconds"),)}),
    )

    def get_urls(self):  # type: ignore[no-untyped-def]
        from .urls import urlpatterns as chart_urls
        return chart_urls + super().get_urls()

    @admin.display(description="Chart")
    def chart_link(self, obj: TimeSeriesChart):
        return html_link(reverse("admin:admin_extended_charts_chart", args=[obj.pk]), title="View chart")
```

- [ ] **Step 2: Write chart.html**

```html
{% extends "admin/base_site.html" %}
{% block content %}
<h1>{{ chart_title }}</h1>
<form method="get">{{ form.as_p }}<button type="submit">Apply</button></form>
<canvas id="chart-canvas"></canvas>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4"></script>
<script>
(async () => {
  const params = new URLSearchParams(window.location.search);
  const url = "{{ metrics_url }}" + "?" + params.toString();
  const r = await fetch(url);
  if (!r.ok) { document.getElementById("chart-canvas").outerHTML = "Error loading chart"; return; }
  const j = await r.json();
  new Chart(document.getElementById("chart-canvas"), {
    type: (j.chart_type || "BAR").toLowerCase(),
    data: {
      labels: j.labels,
      datasets: j.datasets.map(d => ({ label: d.label, data: d.data })),
    },
    options: { scales: { x: { stacked: !!j.stacked }, y: { stacked: !!j.stacked } } },
  });
})();
</script>
{% endblock %}
```

- [ ] **Step 3: Run view tests**

```bash
pytest admin_extended/tests/test_charts_views.py -v
```

Expected: 4 passed.

### Task 10.10: Commit Phase 10

```bash
git add admin_extended/charts admin_extended/tests/test_charts_*.py admin_extended/tests/example_project/settings.py
git commit -m "feat(charts): split into sub-app with service layer + clean() validation"
```

---

## Phase 11: Theme assets — templatetags, template overrides, static

Migrates v5's `admin_extended/templatetags/sort_menu_items.py` and `settings_value.py` to the new naming and adds bookmark-tolerance (H5) + cache (B11).

### Task 11.1: Test admin_extended_menu templatetag

**Files:**
- Create: `admin_extended/tests/test_theme_menu.py`

- [ ] **Step 1: Write tests**

```python
"""Tests for the sidebar menu templatetag."""
from __future__ import annotations

from django.test import override_settings

from admin_extended.bookmarks.models import Bookmark
from admin_extended.templatetags.admin_extended_menu import sort_apps, sort_models


@override_settings(ADMIN_EXTENDED={
    "MENU_APP_ORDER": ["sample_app", "auth"],
    "APP_ICON": {"sample_app": "fas fa-flask"},
})
def test_sort_apps_respects_order_and_icon():
    apps = [
        {"app_label": "auth", "name": "Auth"},
        {"app_label": "sample_app", "name": "Sample"},
        {"app_label": "other", "name": "Other"},
    ]
    sorted_apps = sort_apps(apps)
    labels = [a["app_label"] for a in sorted_apps]
    # sample_app first, auth second, other last
    assert labels.index("sample_app") < labels.index("auth") < labels.index("other")
    assert next(a for a in sorted_apps if a["app_label"] == "sample_app")["icon"] == "fas fa-flask"


def test_sort_apps_returns_new_list_does_not_mutate_input():
    apps = [{"app_label": "z"}, {"app_label": "a"}]
    out = sort_apps(apps)
    # input is preserved
    assert [a["app_label"] for a in apps] == ["z", "a"]
    assert out is not apps


def test_sort_apps_prepends_bookmark_app_when_bookmarks_exist(db):
    Bookmark.objects.create(name="B", url="https://b", is_active=True, order=1)
    apps = [{"app_label": "sample_app", "name": "Sample"}]
    out = sort_apps(apps)
    assert out[0]["app_label"] == "admin_extended_bookmarks"
    assert out[0]["models"][0]["name"] == "B"


def test_sort_models_orders_by_setting():
    with override_settings(ADMIN_EXTENDED={"MENU_MODEL_ORDER": ["Product", "Order"]}):
        models_list = [{"object_name": "Order"}, {"object_name": "Product"}, {"object_name": "Customer"}]
        out = sort_models(models_list)
        names = [m["object_name"] for m in out]
        assert names.index("Product") < names.index("Order") < names.index("Customer")
```

- [ ] **Step 2: Run to verify it fails**

```bash
pytest admin_extended/tests/test_theme_menu.py -v
```

Expected: ModuleNotFoundError.

### Task 11.2: Implement templatetags

**Files:**
- Create: `admin_extended/templatetags/__init__.py`
- Create: `admin_extended/templatetags/admin_extended_menu.py`
- Create: `admin_extended/templatetags/admin_extended_misc.py`

- [ ] **Step 1: Create dir**

```bash
mkdir -p admin_extended/templatetags
touch admin_extended/templatetags/__init__.py
```

- [ ] **Step 2: Write admin_extended_menu.py**

```python
"""Sidebar app/model ordering + bookmark section (cached + tolerant of missing sub-app)."""
from __future__ import annotations

from typing import Any

from django import template
from django.apps import apps as django_apps
from django.core.cache import cache
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from ..conf import settings as ae_settings

register = template.Library()

_BOOKMARK_CACHE_KEY = "admin_extended:bookmarks:active"


def _load_bookmark_app_entry() -> dict[str, Any] | None:
    if not django_apps.is_installed("admin_extended.bookmarks"):
        return None
    cached = cache.get(_BOOKMARK_CACHE_KEY)
    if cached is not None:
        return cached if cached else None
    Bookmark = django_apps.get_model("admin_extended.bookmarks", "Bookmark")
    bookmarks = list(Bookmark.objects.filter(is_active=True).order_by("order"))
    if not bookmarks:
        cache.set(_BOOKMARK_CACHE_KEY, {}, ae_settings.BOOKMARK_CACHE_SECONDS)
        return None
    entry = {
        "name": "Bookmark",
        "icon": "fas fa-bookmark",
        "app_label": "admin_extended_bookmarks",
        "app_url": "/admin/admin_extended_bookmarks/bookmark/",
        "has_module_perms": True,
        "models": [
            {
                "name": b.name,
                "object_name": b.name,
                "perms": {"add": False, "change": False, "delete": False, "view": True},
                "admin_url": b.url,
                "view_only": True,
            }
            for b in bookmarks
        ],
    }
    cache.set(_BOOKMARK_CACHE_KEY, entry, ae_settings.BOOKMARK_CACHE_SECONDS)
    return entry


def _attach_metadata(app: dict[str, Any]) -> dict[str, Any]:
    out = dict(app)
    if out.get("app_label") == "auth":
        out["name"] = "Groups"
    icon_map = ae_settings.APP_ICON
    out["icon"] = icon_map.get(out.get("app_label"), ae_settings.DEFAULT_APP_ICON)
    return out


@register.filter
def sort_apps(apps: list[dict[str, Any]]) -> list[dict[str, Any]]:
    order = ae_settings.MENU_APP_ORDER
    max_index = len(order)
    decorated = [_attach_metadata(a) for a in apps]
    decorated.sort(key=lambda a: order.index(a["app_label"]) if a["app_label"] in order else max_index)

    bookmark_entry = _load_bookmark_app_entry()
    if bookmark_entry:
        return [bookmark_entry, *decorated]
    return decorated


@register.filter
def sort_models(models_list: list[dict[str, Any]]) -> list[dict[str, Any]]:
    order = ae_settings.MENU_MODEL_ORDER
    max_index = len(order)
    return sorted(
        models_list,
        key=lambda m: order.index(m["object_name"]) if m["object_name"] in order else max_index,
    )


# ---- cache invalidation on Bookmark write ---------------------------------

if django_apps.is_installed("admin_extended.bookmarks"):
    Bookmark = django_apps.get_model("admin_extended.bookmarks", "Bookmark")

    @receiver(post_save, sender=Bookmark)
    @receiver(post_delete, sender=Bookmark)
    def _invalidate_bookmark_cache(sender, **kwargs):  # type: ignore[no-untyped-def]
        cache.delete(_BOOKMARK_CACHE_KEY)
```

- [ ] **Step 3: Write admin_extended_misc.py**

```python
"""Generic helpers: read arbitrary Django settings inside templates."""
from __future__ import annotations

from typing import Any

from django import template
from django.conf import settings

register = template.Library()


@register.simple_tag
def settings_value(name: str, default: Any = None) -> Any:
    if "." not in name:
        return getattr(settings, name, default)
    head, *rest = name.split(".")
    value: Any = getattr(settings, head, None)
    for key in rest:
        if not isinstance(value, dict) or key not in value:
            return default
        value = value[key]
    return value
```

- [ ] **Step 4: Run tests**

```bash
pytest admin_extended/tests/test_theme_menu.py -v
```

Expected: 4 passed.

### Task 11.3: Migrate template overrides

**Files:**
- Create (by copying from v5 with adjustments): `admin_extended/templates/admin/base_site.html`, `app_list.html`, `change_form.html`, `change_list.html`, `search_form.html`

- [ ] **Step 1: Copy v5 templates as starting point**

```bash
cp admin_extended/templates/admin/base_site.html /tmp/v5_base_site.html
cp admin_extended/templates/admin/app_list.html /tmp/v5_app_list.html
cp admin_extended/templates/admin/change_form.html /tmp/v5_change_form.html
cp admin_extended/templates/admin/change_list.html /tmp/v5_change_list.html
cp admin_extended/templates/admin/search_form.html /tmp/v5_search_form.html
```

(The files are already in place from v5. We update them in place.)

- [ ] **Step 2: Update `templates/admin/app_list.html`**

Replace any `{% load sort_menu_items %}` with `{% load admin_extended_menu %}`. The filter names `sort_apps` and `sort_models` are unchanged.

```bash
grep -rln "sort_menu_items" admin_extended/templates/ | xargs sed -i.bak 's/sort_menu_items/admin_extended_menu/g'
find admin_extended/templates -name "*.bak" -delete
```

- [ ] **Step 3: Update any reference to `settings_value` templatetag**

```bash
grep -rln "{% load settings_value %}" admin_extended/templates/ | xargs sed -i.bak 's/{% load settings_value %}/{% load admin_extended_misc %}/g'
find admin_extended/templates -name "*.bak" -delete 2>/dev/null || true
```

- [ ] **Step 4: Update `change_form.html` and `change_list.html` to use new extra_context keys**

Replace template variables that referenced `change_form_object_tools` / `change_form_submit_row` / `change_list_object_tools` with the new namespaced names:

```bash
sed -i.bak 's/change_form_object_tools/admin_extended_object_tools/g' admin_extended/templates/admin/change_form.html
sed -i.bak 's/change_form_submit_row/admin_extended_submit_row_tools/g' admin_extended/templates/admin/change_form.html
sed -i.bak 's/change_list_object_tools/admin_extended_changelist_tools/g' admin_extended/templates/admin/change_list.html
find admin_extended/templates -name "*.bak" -delete
```

- [ ] **Step 5: Update template includes that referenced v5 custom dirs**

```bash
grep -rln "admin/custom/" admin_extended/templates/ | xargs sed -i.bak 's|admin/custom/change_form_submit_row.html|admin/admin_extended/object_tools/change_form_submit_row.html|g'
grep -rln "admin/custom/" admin_extended/templates/ | xargs sed -i.bak 's|admin/custom/custom_object_tools.html|admin/admin_extended/object_tools/change_form_object_tools.html|g'
find admin_extended/templates -name "*.bak" -delete
```

- [ ] **Step 6: Smoke-check that Django loads the admin index without errors**

```bash
python -c "
import os, django
os.environ['DJANGO_SETTINGS_MODULE'] = 'admin_extended.tests.example_project.settings'
django.setup()
from django.test import Client
from django.contrib.auth import get_user_model
User = get_user_model()
User.objects.create_superuser('smoke', 'smoke@example.com', 'pw')
c = Client(); c.login(username='smoke', password='pw')
r = c.get('/admin/')
print('status:', r.status_code)
assert r.status_code == 200
"
```

Note: this is a manual smoke test, not a recurring pytest. If you prefer to leave it to CI, skip; the unit tests cover the templatetags.

### Task 11.4: Verify static assets still in place

- [ ] **Step 1: Check static dir**

```bash
ls admin_extended/static/admin_extended/css/
```

Expected: `theme.css`, `jquery-ui.css`, `extended.css` are present (carried over from v5).

### Task 11.5: Commit Phase 11

```bash
git add admin_extended/templatetags admin_extended/templates admin_extended/tests/test_theme_menu.py
git commit -m "feat(theme): root templatetags + cached bookmark sidebar (B11, H5)"
```

---

## Phase 12: management command + apps.py refresh + remove v5 templatetags

### Task 12.1: Test migration_graph command

**Files:**
- Create: `admin_extended/tests/test_management_migration_graph.py`

- [ ] **Step 1: Write tests**

```python
"""Smoke test for the migration_graph management command."""
from __future__ import annotations

from io import StringIO

from django.core.management import call_command


def test_migration_graph_runs_for_sample_app(db):
    out = StringIO()
    call_command("migration_graph", "sample_app", stdout=out)
    output = out.getvalue()
    assert "Migration graph for sample_app" in output
    assert "0001_initial" in output
```

- [ ] **Step 2: Run to verify it currently fails or passes**

```bash
pytest admin_extended/tests/test_management_migration_graph.py -v
```

The v5 command still exists at `admin_extended/management/commands/migration_graph.py`. It should pass. If the v5 version was already deleted, write the new one in Step 3.

### Task 12.2: Refactor migration_graph with type hints

**Files:**
- Modify: `admin_extended/management/commands/migration_graph.py`

- [ ] **Step 1: Rewrite with type hints + cleaner structure**

```python
"""Print the migration dependency tree for an app."""
from __future__ import annotations

from collections import defaultdict
from typing import Any

from django.core.management.base import AppCommand, CommandParser
from django.db.migrations.loader import MigrationLoader


class Command(AppCommand):
    help = "Show migrations with dependencies for the provided application(s)"

    def add_arguments(self, parser: CommandParser) -> None:
        super().add_arguments(parser)

    def handle(self, *app_labels: str, **options: Any) -> None:
        self.loader = MigrationLoader(None)
        for label in app_labels:
            self._print_graph(label)
            self.stdout.write("")

    # ---- helpers ------------------------------------------------------

    def _print_graph(self, app: str) -> None:
        try:
            root_key = self.loader.graph.root_nodes(app)[0]
        except IndexError:
            self.stdout.write(f"Migrations for `{app}` application were not found")
            return

        root_node = self.loader.graph.node_map[root_key]
        tree: dict[str, list[str]] = defaultdict(list)
        queue = [root_node]
        while queue:
            node = queue.pop(0)
            for child in node.children:
                if child.key[0] == node.key[0] and child not in queue:
                    queue.append(child)
                    tree[node.key[1]].append(child.key[1])

        self.stdout.write(self.style.SUCCESS(f"Migration graph for {app}"))
        self._print_tree(root_node.key[1], tree)

    def _print_tree(self, start: str, tree: dict[str, list[str]], indent: str = "") -> None:
        self.stdout.write(self.style.SUCCESS(start))
        self._walk(start, tree, indent)

    def _walk(self, parent: str, tree: dict[str, list[str]], indent: str) -> None:
        children = tree.get(parent, [])
        if not children:
            return
        child_style = self.style.ERROR if len(children) > 1 else self.style.SUCCESS
        for i, child in enumerate(children):
            is_last = i == len(children) - 1
            connector = "└─" if is_last else "├─"
            self.stdout.write(f"{indent}{connector} {child_style(child)}")
            next_indent = indent + ("  " if is_last else "│ ")
            self._walk(child, tree, next_indent)
```

- [ ] **Step 2: Run tests**

```bash
pytest admin_extended/tests/test_management_migration_graph.py -v
```

Expected: 1 passed.

### Task 12.3: Update apps.py

**Files:**
- Modify: `admin_extended/apps.py`

- [ ] **Step 1: Write apps.py**

```python
from __future__ import annotations

from django.apps import AppConfig


class AdminExtendedConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "admin_extended"
    label = "admin_extended"
    verbose_name = "Admin Extended"
```

### Task 12.4: Refresh __init__.py

**Files:**
- Modify: `admin_extended/__init__.py`

- [ ] **Step 1: Write __init__.py**

```python
"""django-admin-extended — UI/UX enhancements for the Django admin."""
from __future__ import annotations

try:
    from ._version import version as __version__  # written by setuptools-scm
except ImportError:  # pragma: no cover
    __version__ = "0.0.0+unknown"

default_app_config = "admin_extended.apps.AdminExtendedConfig"

__all__ = ["__version__", "default_app_config"]
```

### Task 12.5: Commit Phase 12

```bash
git add admin_extended/__init__.py admin_extended/apps.py admin_extended/management/commands/migration_graph.py admin_extended/tests/test_management_migration_graph.py
git commit -m "refactor(mgmt): type hints + cleanup for migration_graph; refresh apps.py / __init__"
```

---

## Phase 13: Dependency-rule enforcement test

### Task 13.1: Test that no upward imports exist

**Files:**
- Create: `admin_extended/tests/test_imports.py`

- [ ] **Step 1: Write test**

```python
"""Enforce subsystem dependency rules.

Allowed imports (target -> sources that may import it):
  conf            <- core, display, charts, bookmarks, theme templatetags
  display         <- core, charts
  core            <- object_tools, autoregister, custom_pages, charts
  bookmarks       <- (sub-app, no upstream)
  charts          <- (sub-app, no upstream)

Forbidden:
  conf importing anything from admin_extended
  core importing object_tools / autoregister / custom_pages / bookmarks / charts
  display importing core / object_tools / autoregister / custom_pages / bookmarks / charts
  bookmarks importing core / object_tools / autoregister / custom_pages / charts / display
"""
from __future__ import annotations

import ast
import os
from pathlib import Path

ROOT = Path("admin_extended")

FORBIDDEN: dict[str, tuple[str, ...]] = {
    "admin_extended/conf.py": (
        "admin_extended.core", "admin_extended.display", "admin_extended.object_tools",
        "admin_extended.autoregister", "admin_extended.custom_pages",
        "admin_extended.bookmarks", "admin_extended.charts",
    ),
    "admin_extended/core/": (
        # core composes ObjectToolMixin into ExtendedAdminModel — that is allowed.
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
```

Note: `core` composing `object_tools.mixin.ObjectToolMixin` into `ExtendedAdminModel` is intentional and allowed by the rule above. The leaf-vs-feature direction is "core uses object_tools' mixin", not "object_tools uses core". `ObjectToolMixin` itself imports nothing from `core`, so no cycle.

- [ ] **Step 2: Run the import test**

```bash
pytest admin_extended/tests/test_imports.py -v
```

Expected: 1 passed. If it fails, the message will name the violating file/module — fix that import or update the FORBIDDEN map after design review.

### Task 13.2: Run full suite

```bash
pytest -x
```

Expected: all tests in all modules pass.

### Task 13.3: Commit Phase 13

```bash
git add admin_extended/tests/test_imports.py
git commit -m "test: enforce subsystem dependency rules"
```

---

## Phase 14: Cleanup, docs, release tag

### Task 14.1: Delete v5 source files

**Files:**
- Delete: `admin_extended/base/` (entire directory)
- Delete: `admin_extended/admin/` (entire directory)
- Delete: `admin_extended/models/` (entire directory)
- Delete: `admin_extended/utils.py`
- Delete: `admin_extended/decorators.py`
- Delete: `admin_extended/settings.py`
- Delete: `admin_extended/templatetags/sort_menu_items.py`
- Delete: `admin_extended/templatetags/settings_value.py`
- Delete: `admin_extended/migrations/0001_initial.py`, `0002_timeserieschart.py` (the v5 chart/bookmark migrations — bookmarks and charts are now sub-apps with their own migration packages)

- [ ] **Step 1: Verify nothing in v6 still imports v5 paths**

```bash
grep -rn "admin_extended.base\|admin_extended.utils\|admin_extended.decorators\|admin_extended.settings\b\|admin_extended.admin\.\|admin_extended.models\." admin_extended/ --include "*.py" | grep -v "tests/" | grep -v "_version.py" | grep -v "/migrations/"
```

Expected: no output. If any line appears, fix the import before deleting.

- [ ] **Step 2: Delete**

```bash
git rm -r admin_extended/base admin_extended/admin admin_extended/models
git rm admin_extended/utils.py admin_extended/decorators.py admin_extended/settings.py
git rm admin_extended/templatetags/sort_menu_items.py admin_extended/templatetags/settings_value.py
git rm admin_extended/migrations/0001_initial.py admin_extended/migrations/0002_timeserieschart.py
# Also delete the now-empty migrations dir's __init__ if present in v5 root
git rm admin_extended/migrations/__init__.py 2>/dev/null || true
# Remove the directory if empty
rmdir admin_extended/migrations 2>/dev/null || true
```

- [ ] **Step 3: Run full suite to confirm nothing was missed**

```bash
pytest -x
```

Expected: all tests pass.

### Task 14.2: Update CLAUDE.md

**Files:**
- Modify: `CLAUDE.md`

- [ ] **Step 1: Rewrite CLAUDE.md content**

Replace the file with content reflecting the v6 architecture. Key changes from v5:
- Mention `INSTALLED_APPS` requires `admin_extended` and optionally `admin_extended.bookmarks`, `admin_extended.charts`.
- New module map (core / display / object_tools / autoregister / custom_pages / bookmarks / charts).
- Settings via `from admin_extended.conf import settings as ae_settings`.
- Page mode via `from admin_extended.core import get_page_mode, PageMode`.
- New attribute names on `ExtendedAdminModel` (view_only_fields, edit_only_fields, etc.).
- Test runner: `pytest` or `tox`.
- No `setup.py`; build via `python -m build`.

A concrete suggested contents (write this verbatim):

```markdown
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
- `admin_extended.core`: `ExtendedAdminModel`, `PageMode`, `get_page_mode`, fieldset filters, `delete_without_confirm` action.
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
```

### Task 14.3: Update llms.txt

**Files:**
- Modify: `llms.txt`

- [ ] **Step 1: Replace v5 API references with v6**

Open `llms.txt`; replace all references to v5 paths (`admin_extended.base`, `ext_read_only_fields`, etc.) with the v6 equivalents from the spec's Rename Table. Key updates:

- `from admin_extended.base import ExtendedAdminModel` → `from admin_extended.core import ExtendedAdminModel`
- `ext_read_only_fields` → `view_only_fields`
- `ext_write_only_fields` → `edit_only_fields`
- `super_admin_only_fields` → `superuser_only_fields`
- `tab_inline` → `tabbed_inlines`
- `delete_without_confirm` (class attr) → `skip_delete_confirm`
- `raw_id_fields_as_default` → `auto_raw_id_fields`
- `MODEL_ADMIN_TABBED_INLINE` setting → `TABBED_INLINES`
- `RAW_ID_FIELDS_AS_DEFAULT` setting → `AUTO_RAW_ID_FIELDS`
- `@object_tool(description=...)` → `@object_tool(label=...)`
- `@object_tool(http_method=...)` → `@object_tool(method=...)`
- `auto_register_model_admin` → `auto_register`
- `DispayLinkAdapter` → `DisplayLinkAdapter`

Add an INSTALLED_APPS note that bookmarks and charts are now sub-apps.

### Task 14.4: Write CHANGELOG.md

**Files:**
- Create: `CHANGELOG.md`

- [ ] **Step 1: Write CHANGELOG with v6.0.0 entry**

```markdown
# Changelog

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [6.0.0] — 2026-XX-XX

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
- `ExtendedAdminModel.get_html_*` methods (use free functions `admin_extended.display.html_*`).
- `ExtendedAdminModel.TEXT_COLOR_*` constants (use `admin_extended.display.html.{SUCCESS,ERROR,WARNING,DEFAULT}`).
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
```

### Task 14.5: Write CONTRIBUTING.md

**Files:**
- Create: `CONTRIBUTING.md`

- [ ] **Step 1: Write content**

```markdown
# Contributing

## Dev setup

```bash
pip install -e ".[dev]"
```

## Run tests

```bash
pytest                                       # one Python/Django combo (whatever you installed)
tox                                          # full matrix + lint + type + build
tox -e py312-dj52                            # one matrix cell
tox -e lint                                  # ruff check + format
tox -e type                                  # mypy strict
```

## Style

- `ruff format` formats code; CI requires `ruff format --check` to pass.
- `ruff check` lints; configuration is in `pyproject.toml`.
- All new public code requires type hints. `mypy --strict` runs in CI.

## Adding a feature

Place new code in the appropriate subsystem under `admin_extended/`. Subsystem
boundaries are enforced by `admin_extended/tests/test_imports.py`. If your
change requires a new dependency direction, update the FORBIDDEN map there
with a comment explaining why.
```

### Task 14.6: Tag v6.0.0

- [ ] **Step 1: Final commit**

```bash
git add CLAUDE.md llms.txt CHANGELOG.md CONTRIBUTING.md
git commit -m "docs: update CLAUDE.md, llms.txt, CHANGELOG.md, CONTRIBUTING.md for v6"
```

- [ ] **Step 2: Run full suite one last time**

```bash
pytest -x && tox -e lint && tox -e type && tox -e build
```

Expected: all green.

- [ ] **Step 3: Tag**

```bash
git tag -a v6.0.0 -m "v6.0.0 — architecture refactor (see CHANGELOG.md)"
```

Do **not** push the tag automatically — leave that to the operator.

---

## Done

All 13 phases complete. The v6.0.0 tree:

- Boots cleanly under Python 3.12/3.13 and Django 5.2/6.0.
- Passes `pytest`, `tox -e lint`, `tox -e type`, `tox -e build`.
- Has no upward imports between subsystems (`test_imports.py`).
- Ships templates and static via `pyproject.toml` `package-data` for the main app and both sub-apps.
- Has full type hints + `py.typed`.

Consumers install via:

```bash
pip install "git+https://github.com/cuongnb14/django-admin-extended.git@v6.0.0"
```
