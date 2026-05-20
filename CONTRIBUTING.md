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
