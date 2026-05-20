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
