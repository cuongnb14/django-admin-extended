"""Smoke tests for the create_db management command error paths.

The CREATE DATABASE path requires a live PostgreSQL/MySQL server and is not
exercised here; these cover the argument and engine validation only.
"""
from __future__ import annotations

import pytest
from django.core.management import call_command
from django.core.management.base import CommandError


def test_create_db_unknown_alias():
    with pytest.raises(CommandError, match="not found in settings.DATABASES"):
        call_command("create_db", "--database", "nope")


def test_create_db_unsupported_engine():
    # The test project uses the sqlite3 backend, which create_db does not support.
    with pytest.raises(CommandError, match="Unsupported ENGINE"):
        call_command("create_db")
