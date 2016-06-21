from __future__ import print_function

import re

class TreePattern:
    """
    Base class for a tree pattern.
    Tree pattern matches a single node in dependency tree.
    """

    def match(self, tree, node, backrefs_map):
        """
        Return whether a node matches this pattern.

        - tree: a Tree
        - node: node index (1-based, 0 means "root") to match on
        - backrefs_map: contains backreferences to nodes in tree
          (dict: unicode -> int), which will be available after the
          whole-pattern match. Backreferences also can be used to communicate
          with sub-patterns (see e.g. SetBackref and EqualsBackref).

          All patterns should comply with the invariant:

          * If pattern not matches, backrefs_map should be left intact.
          * If pattern matches, it may write something to backrefs_map.
        """
        raise NotImplementedError()

def compile_regex(pattern, ignore_case, anywhere):
    """
    Return Python compiled regex. Match your string against it with
    'r.search(s)'.

    - ignore_case: ignore case of s.
    - anywhere: if False, r.search(s) does a whole-string match.
    """
    flags = re.UNICODE
    if ignore_case:
        flags = flags | re.IGNORECASE
    if not anywhere:
        pattern = '^' + pattern + '$'
    return re.compile(pattern, flags)

## ----------------------------------------------------------------------------
#                                  Children

class HasLeftChild(TreePattern):
    def __init__(self, condition):
        self.condition = condition

    def match(self, tree, node, backrefs_map):
        for child in tree.children(node):
            if child > node:
                continue
            if self.condition.match(tree, child, backrefs_map):
                return True
        return False

class HasRightChild(TreePattern):
    def __init__(self, condition):
        self.condition = condition

    def match(self, tree, node, backrefs_map):
        for child in tree.children(node):
            if child < node:
                continue
            if self.condition.match(tree, child, backrefs_map):
                return True
        return False

class HasChild(TreePattern):
    def __init__(self, condition):
        self.condition = condition

    def match(self, tree, node, backrefs_map):
        for child in tree.children(node):
            if self.condition.match(tree, child, backrefs_map):
                return True
            return False

class HasSuccessor(TreePattern):
    def __init__(self, condition):
        self.condition = condition

    def match(self, tree, node, backrefs_map):
        for child in tree.children_recursive(node):
            if self.condition.match(tree, child, backrefs_map):
                return True
        return False

class HasAdjacentLeftChild(TreePattern):
    def __init__(self, condition):
        self.condition = condition

    def match(self, tree, node, backrefs_map):
        for child in tree.children(node):
            if child + 1 != node:
                continue
            if self.condition.match(tree, child, backrefs_map):
                return True
        return False

class HasAdjacentRightChild(TreePattern):
    def __init__(self, condition):
        self.condition = condition

    def match(self, tree, node, backrefs_map):
        for child in tree.children(node):
            if child - 1 != node:
                continue
            if self.condition.match(tree, child, backrefs_map):
                return True
        return False

class HasAdjacentChild(TreePattern):
    def __init__(self, condition):
        self.condition = condition

    def match(self, tree, node, backrefs_map):
        for child in tree.children(node):
            if (child - node) not in [-1, +1]:
                continue
            if self.condition.match(tree, child, backrefs_map):
                return True
        return False

## ----------------------------------------------------------------------------
#                                   Parents

class HasLeftHead(TreePattern):
    def __init__(self, condition):
        self.condition = condition

    def match(self, tree, node, backrefs_map):
        if node == 0:
            return False

        head = tree.heads(node)
        return head < node and self.condition.match(tree, head, backrefs_map)

class HasRightHead(TreePattern):
    def __init__(self, condition):
        self.condition = condition

    def match(self, tree, node, backrefs_map):
        if node == 0:
            return False

        head = tree.heads(node)
        return head > node and self.condition.match(tree, head, backrefs_map)

class HasHead(TreePattern):
    def __init__(self, condition):
        self.condition = condition

    def match(self, tree, node, backrefs_map):
        if node == 0:
            return False

        head = tree.heads(node)
        return self.condition.match(tree, head, backrefs_map)

class HasPredecessor(TreePattern):
    def __init__(self, condition):
        self.condition = condition

    def match(self, tree, node, backrefs_map):
        while True:
            node = tree.heads(node)
            if self.condition.match(tree, node, backrefs_map):
                return True
            if node == 0:
                break
        return False

class HasAdjacentLeftHead(TreePattern):
    def __init__(self, condition):
        self.condition = condition

    def match(self, tree, node, backrefs_map):
        if node == 0:
            return False

        head = tree.heads(node)
        adjacent = (head + 1 == node)
        return adjacent and self.condition.match(tree, head, backrefs_map)

class HasAdjacentRightHead(TreePattern):
    def __init__(self, condition):
        self.condition = condition

    def match(self, tree, node, backrefs_map):
        if node == 0:
            return False

        head = tree.heads(node)
        adjacent = (head - 1 == node)
        return adjacent and self.condition.match(tree, head, backrefs_map)

class HasAdjacentHead(TreePattern):
    def __init__(self, condition):
        self.condition = condition

    def match(self, tree, node, backrefs_map):
        if node == 0:
            return False

        head = tree.heads(node)
        adjacent = (head - node) in [-1, +1]
        return adjacent and self.condition.match(tree, head, backrefs_map)

## ----------------------------------------------------------------------------
#                                 Neighbors

class HasLeftNeighbor(TreePattern):
    def __init__(self, condition):
        self.condition = condition

    def match(self, tree, node, backrefs_map):
        if node == 0:
            return False

        for neighbor in range(0, node):
            if self.condition.match(tree, neighbor, backrefs_map):
                return True
        return False

class HasRightNeighbor(TreePattern):
    def __init__(self, condition):
        self.condition = condition

    def match(self, tree, node, backrefs_map):
        for neighbor in range(node + 1, len(tree) + 1):
            if self.condition.match(tree, neighbor, backrefs_map):
                return True
        return False

class HasAdjacentLeftNeighbor(TreePattern):
    def __init__(self, condition):
        self.condition = condition

    def match(self, tree, node, backrefs_map):
        if node == 0:
            return False

        neighbor = node - 1
        return self.condition.match(tree, neighbor, backrefs_map)

class HasAdjacentRightNeighbor(TreePattern):
    def __init__(self, condition):
        self.condition = condition

    def match(self, tree, node, backrefs_map):
        if node == len(tree):
            return False

        neighbor = node + 1
        return self.condition.match(tree, neighbor, backrefs_map)

## ----------------------------------------------------------------------------
#                            Misc. tree structure

class CanHead(TreePattern):
    def __init__(self, backref):
        self.backref = backref

    def match(self, tree, node, backrefs_map):
        if self.backref not in backrefs_map:
            return False

        head = node
        child = backrefs_map[self.backref]
        return head not in [child] + tree.children_recursive(child)

class CanBeHeadedBy(TreePattern):
    def __init__(self, backref):
        self.backref = backref

    def match(self, tree, node, backrefs_map):
        if self.backref not in backrefs_map:
            return False

        head = backrefs_map[self.backref]
        child = node
        return head not in [child] + tree.children_recursive(child)

class IsRoot(TreePattern):
    def match(self, tree, node, backrefs_map):
        return node == 0

class NotRoot(TreePattern):
    def __init__(self, condition):
        self.condition = condition

    def match(self, tree, node, backrefs_map):
        return node != 0 and self.condition.match(tree, node, backrefs_map)

class IsTop(TreePattern):
    def match(self, tree, node, backrefs_map):
        return node != 0 and tree.heads(node) == 0

class IsLeaf(TreePattern):
    def match(self, tree, node, backrefs_map):
        return not tree.children(node)

## ----------------------------------------------------------------------------
#                                 Attributes

class AttrMatches(TreePattern):
    def __init__(self, attr, pred_fn):
        self.attr = attr
        self.pred_fn = pred_fn

    def match(self, tree, node, backrefs_map):
        if node == 0:
            return False

        attr = getattr(tree, self.attr)(node)
        return self.pred_fn(attr)

class FeatsMatch(TreePattern):
    def __init__(self, pred_fn):
        self.pred_fn = pred_fn

    def match(self, tree, node, backrefs_map):
        if node == 0:
            return False

        attr = u'|'.join(tree.feats(node))
        return self.pred_fn(attr)

## ----------------------------------------------------------------------------
#                                   Logic

class And(TreePattern):
    def __init__(self, conditions):
        self.conditions = conditions

    def match(self, tree, node, backrefs_map):
        # Backup the initial backrefs map.
        old_map = backrefs_map.copy()

        for condition in self.conditions:
            if not condition.match(tree, node, backrefs_map):
                # Before returning, restore the old map, i.e. undo all changes
                # to backrefs_map.
                backrefs_map.clear()
                backrefs_map.update(old_map)
                return False
        return True

class Or(TreePattern):
    def __init__(self, conditions):
        self.conditions = conditions

    def match(self, tree, node, backrefs_map):
        for condition in self.conditions:
            if condition.match(tree, node, backrefs_map):
                return True
        return False

class Not(TreePattern):
    def __init__(self, condition):
        self.condition = condition

    def match(self, tree, node, backrefs_map):
        # If sub-condition matchesm 'not sub-condition' doesn't. Sub-condition
        # might modify the backrefs_map on successful match, but since
        # 'not sub-condition' doesn't match, these changes shouldn't be visible
        # to the outside world.
        copy = backrefs_map.copy()
        return not self.condition.match(tree, node, copy)

class AlwaysTrue(TreePattern):
    def match(self, tree, node, backrefs_map):
        return True

## ----------------------------------------------------------------------------
#                                  Backrefs

class SetBackref(TreePattern):
    def __init__(self, backref, condition):
        self.backref = backref
        self.condition = condition

    def match(self, tree, node, backrefs_map):
        # Backup the old backreference value.
        old_backref = backrefs_map.get(self.backref)

        # Update the backref so the underlying condition can see it.
        backrefs_map[self.backref] = node

        # If condition fails, undo the changes to backrefs_map.
        if not self.condition.match(tree, node, backrefs_map):
            if old_backref is None:
                # If there were no such key in the map, delete it.
                del backrefs_map[self.backref]
            else:
                # If there was such key in the map, just restore it.
                backrefs_map[self.backref] = old_backref
            return False
        return True

class EqualsBackref(TreePattern):
    def __init__(self, backref):
        self.backref = backref

    def match(self, tree, node, backrefs_map):
        return backrefs_map.get(self.backref) == node
