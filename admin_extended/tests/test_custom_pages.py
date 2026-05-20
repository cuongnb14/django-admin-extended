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
