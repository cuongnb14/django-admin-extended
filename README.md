# django-admin-extended

Enhance UI/UX of Django admin.

## Installation

```bash
pip install "git+https://github.com/cuongnbms/django-admin-extended.git@v6.0.0"
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

## Using with coding agents

`llms.md` (at the repo root) is a single-file reference that documents every public API, configuration key, and template hook in this package — formatted for LLM consumption.

When working with Claude Code, Cursor, Copilot, or any other coding agent, point it at `llms.md` so it has accurate, version-matched context for the install you're using:

```text
# In your project, fetch the matching version into the agent's context:
curl -O https://raw.githubusercontent.com/cuongnbms/django-admin-extended/v6.0.0/llms.md
```

Or paste the file's URL/contents into the agent at the start of a session. This avoids the agent hallucinating outdated v5-style APIs or invented setting keys.
