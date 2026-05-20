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
