import collections

class TreeState:
    """
    Class for simultaneously manipulating a dependency tree and a
    backreference map.

    E.g. if you have a map {'x': 12}, and you move node #12 to the beginning
    of the sentence so that it becomes #1, you should update backreference map:
    {'x': 1}.

    Also can mark and group nodes together,
    """

    def __init__(self, tree, backrefs_map):
        self.tree = tree
        self.backrefs_map = backrefs_map
        self._marked = set()
        self._grouped_with = collections.defaultdict(set)

    # - Modifications - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def move(self, nodes, anchor, where):
        """
        Move nodes in the tree.
        Re-adjust backrefs, groupings, and markings as well.
        """
        # Reorder tree.
        new_indices = self.tree.move(nodes, anchor, where)

        # Reorder marks.
        marked = set()
        for node in self._marked:
            if node != 0:
                node = new_indices[node - 1] + 1
            marked.add(node)
        self._marked = marked

        # Reorder grouping.
        grouped_with = collections.defaultdict(set)
        for node, grouped_nodes in self._grouped_with.items():
            if node != 0:
                node = new_indices[node - 1] + 1
            for grouped_node in grouped_nodes:
                if grouped_node != 0:
                    grouped_node = new_indices[grouped_node - 1] + 1
                grouped_with[node].add(grouped_node)
        self._grouped_with = grouped_with

    def delete(self, nodes):
        """
        Remove nodes in the tree.
        Remove backrefs, groupings, and markings as well.
        """
        if not isinstance(nodes, (list, tuple, set)):
            nodes = [nodes]

        # Truncate the tree.
        deleted = set(nodes)
        self.tree.delete(deleted)

        # Erase marks and groupings.
        for node in deleted:
            if node in self._marked:
                self._marked.remove(node)

        # Erase groupings.
        for node in deleted:
            if node in self._grouped_with:
                for grouped_node in self._grouped_with[node]:
                    self._grouped_with[grouped_node].remove(node)
                del self._grouped_with[node]

        # Erase backrefs.
        backrefs_to_erase = []
        for backref, node in self.backrefs_map.items():
            if node in deleted:
                backrefs_to_erase.append(backref)
        for backref in backrefs_to_erase:
            del self.backrefs_map[backref]

    # - Marks - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def mark(self, node):
        """
        Flag a tree node.
        """
        self._marked.add(node)

    def marked(self, node):
        """
        Check whether a node has the flag set.
        """
        return node in self._marked

    def unmark(self, node):
        """
        Reset flag on a tree node.
        """
        if node in self._marked:
            self._marked.remove(node)

    def unmark_all(self):
        """
        Reset flags on all nodes.
        """
        self._marked.clear()

    # - Grouping  - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def group_together(self, node1, node2):
        """
        For the purposes of gather_group(), always add node1 to the result of
        gather_group(node2) and vice versa.
        """
        self._grouped_with[node1].add(node2)
        self._grouped_with[node2].add(node1)

    def gather_group(self, node):
        """
        Return node, groups of its children (recursively), nodes that were
        explicitly grouped with group_together(), and groups of their children
        (also recursively).
        """
        indices = [node]
        visited = set()

        i = 0
        while i < len(indices):
            node = indices[i]
            i += 1

            # Check visited.
            if node in visited:
                continue
            visited.add(node)

            # Recurse.
            indices.extend(self.tree.children(node))
            indices.extend(self._grouped_with.get(node, []))


        return indices
