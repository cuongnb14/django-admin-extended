from collections import defaultdict

from django.core.management.base import AppCommand
from django.db.migrations.loader import MigrationLoader


class Command(AppCommand):
    help = 'Show migrations with dependencies for provided applications '

    def handle(self, *apps, **options):
        self.loader = MigrationLoader(None)
        for app in apps:
            self._print_app_migrations_graph(app)
            self.stdout.write('\n')

    def _is_same_app(self, node1, node2):
        return node1.key[0] == node2.key[0]

    def _print_app_migrations_graph(self, app):
        try:
            root_key = self.loader.graph.root_nodes(app)[0]
        except IndexError:
            print('Migrations for `{}` application were not found'.format(app))
            return

        root_node = self.loader.graph.node_map[root_key]
        nodes_to_process = [root_node]
        tree = defaultdict(list)

        while nodes_to_process:
            curr_node = nodes_to_process.pop(0)
            for child in curr_node.children:
                if (self._is_same_app(child, curr_node)) and (child not in nodes_to_process):
                    nodes_to_process.append(child)
                    tree[self._get_tree_key(curr_node)].append(self._get_tree_key(child))

        print(f'Migration graph for {app}')
        self._print_tree(self._get_tree_key(root_node), tree)

    def _get_tree_key(self, node):
        return node.key[1]

    def _print_node_with_style(self, style, node, ending='\n'):
        self.stdout.write(style(node), ending=ending)

    def _print_tree(self, start, tree, indent_width=1):

        def _ptree(start, parent, tree, grandpa=None, indent='', style=self.style.SUCCESS):
            if parent != start:
                if grandpa is None:
                    self._print_node_with_style(style, parent, ending='')
                else:
                    self._print_node_with_style(style, parent)
            if parent not in tree:
                return

            if len(tree[parent]) > 1:
                child_style = self.style.ERROR
            else:
                child_style = style

            for child in tree[parent][:-1]:
                print(indent + '├' + '─' * indent_width, end=' ')
                _ptree(start, child, tree, parent, indent + '│' + ' ' * 1, style=child_style)
            child = tree[parent][-1]
            print(indent + '└' + '─' * indent_width, end=' ')
            _ptree(start, child, tree, parent, indent + ' ' * 1, style=child_style)

        parent = start
        self._print_node_with_style(self.style.SUCCESS, start)
        _ptree(start, parent, tree)
