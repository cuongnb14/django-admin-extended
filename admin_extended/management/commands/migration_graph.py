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
