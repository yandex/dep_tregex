def _check_is_not_a_str_list(l, name):
    if l and all(isinstance(s, str) for s in l):
        raise ValueError((
            "'%s' is a list of 'str', not a list of 'unicode'. "
            "Please don't use non-unicode strings in Python 2.7. "
            "To convert 'str' to 'unicode', use s.decode('utf-8')."
            ) % name)

class Tree:
    # - Constructor - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def __init__(self, forms, lemmas, cpostags, postags, feats, heads, deprels):
        """
        Construct a tree.

        forms: list of 'unicode'.
        lemmas: list of 'unicode'.
        cpostags: list of 'unicode'.
        postags: list of 'unicode'.
        feats: list of featuresets; each featureset is a list of 'unicode'.
        head: list of int
        deprels: list of 'unicode'
        """

        # Store.
        self._forms = list(forms)
        self._lemmas = list(lemmas)
        self._cpostags = list(cpostags)
        self._postags = list(postags)
        self._feats = list(feats)
        self._heads = list(heads)
        self._deprels = list(deprels)

        # Check lengths.
        N = len(self._forms)
        msg = 'invalid %s: %r. Expected %i elements.'
        if len(self._lemmas) != N:
            raise ValueError(msg % ('lemmas', self._lemmas, N))
        if len(self._cpostags) != N:
            raise ValueError(msg % ('cpostags', self._cpostags, N))
        if len(self._postags) != N:
            raise ValueError(msg % ('postags', self._postags, N))
        if len(self._feats) != N:
            raise ValueError(msg % ('feats', self._feats, N))
        if len(self._heads) != N:
            raise ValueError(msg % ('heads', self._heads, N))
        if len(self._deprels) != N:
            raise ValueError(msg % ('deprels', self._deprels, N))

        # Check indices.
        if not all(0 <= head <= N for head in self._heads):
            msg = 'invalid heads in %i-word tree: %r'
            raise ValueError(msg % (N, self._heads))

        # Check unicodeness.
        _check_is_not_a_str_list(self._forms, 'Tree.forms')
        _check_is_not_a_str_list(self._lemmas, 'Tree.forms')
        _check_is_not_a_str_list(self._cpostags, 'Tree.cpostags')
        _check_is_not_a_str_list(self._postags, 'Tree.postags')
        _check_is_not_a_str_list(self._feats, 'Tree.feats')
        _check_is_not_a_str_list(self._heads, 'Tree.heads')
        _check_is_not_a_str_list(self._deprels, 'Tree.deprels')

        # Compose children index.
        self._children = [[] for node in range(N + 1)]
        for node, head in enumerate(self._heads, start=1):
            self._children[head].append(node)

        # Check tree validity: connectivity and looplessness.
        queue = [0]
        visited = set()
        i = 0

        while i < len(queue):
            node = queue[i]
            visited.add(node)
            i += 1

            for child in self.children(node):
                if child in visited:
                    raise ValueError('loop in a tree; heads %r' % self._heads)
                queue.append(child)

        if len(queue) != len(self) + 1:
            raise ValueError('dicsonnected node, heads %r' % self._heads)

    # - Getters - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def __len__(self):
        """
        Return number of words in the tree.
        """
        return len(self._forms)

    def forms(self, i):
        """
        Return FORM for i'th word.
        i is 1-based.
        """
        if i <= 0:
            raise IndexError()
        return self._forms[i - 1]

    def lemmas(self, i):
        """
        Return LEMMA for i'th word.
        i is 1-based.
        """
        if i <= 0:
            raise IndexError()
        return self._lemmas[i - 1]

    def cpostags(self, i):
        """
        Return CPOSTAG for i'th word.
        i is 1-based.
        """
        if i <= 0:
            raise IndexError()
        return self._cpostags[i - 1]

    def postags(self, i):
        """
        Return POSTAG for i'th word.
        i is 1-based.
        """
        if i <= 0:
            raise IndexError()
        return self._postags[i - 1]

    def feats(self, i):
        """
        Return FEATS for i'th word, a list of string features.
        i is 1-based.
        """
        if i <= 0:
            raise IndexError()
        return self._feats[i - 1]

    def heads(self, i):
        """
        Return HEAD for i'th word.
        i and result are 1-based.
        """
        if i <= 0:
            raise IndexError()
        return self._heads[i - 1]

    def deprels(self, i):
        """
        Return DEPREL for i'th word.
        i is 1-based.
        """
        if i <= 0:
            raise IndexError()
        return self._deprels[i - 1]

    def children(self, i):
        """
        Return a list of children for i'th word.
        i is 1-based; 0 means "root node".
        """
        if i < 0:
            raise IndexError()
        return self._children[i]

    def children_recursive(self, i):
        """
        Return a list of all descendants (children, grandchildren, etc.) for
        i'th word.
        i is 1-based; 0 means "root node".
        """
        result = []
        for child in self.children(i):
            result += [child] + self.children_recursive(child)
        return result

    # - Mutators  - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def append(self, forms, lemmas, cpostags, postags, feats, heads, deprels):
        """
        Append new nodes to the tree.
        Arguments are the same as in constructor.
        """
        self.__init__(
            self._forms + list(forms),
            self._lemmas + list(lemmas),
            self._cpostags + list(cpostags),
            self._postags + list(postags),
            self._feats + list(feats),
            self._heads + list(heads),
            self._deprels + list(deprels)
            )

    def reorder(self, new_index_by_old_index):
        """
        Reorder nodes in the tree.
        Indices are 0-based.
        """
        N = len(self)
        new_indices = new_index_by_old_index

        # Check remapping.
        # - No index should be occupied twice.
        # - No index should left unset.
        exc = ValueError('invalid reordering: %r' % new_indices)
        if len(set(new_indices)) != N:
            raise exc
        if sorted(new_indices) != range(N):
            raise exc

        # Reorder tree.
        forms = [None] * N
        lemmas = [None] * N
        cpostags = [None] * N
        postags = [None] * N
        feats = [None] * N
        heads = [None] * N
        deprels = [None] * N

        for old_index, new_index in enumerate(new_indices):
            old_head = self._heads[old_index]
            if old_head == 0:
                new_head = 0
            else:
                new_head = new_indices[old_head - 1] + 1

            forms[new_index] = self._forms[old_index]
            lemmas[new_index] = self._lemmas[old_index]
            cpostags[new_index] = self._cpostags[old_index]
            postags[new_index] = self._postags[old_index]
            feats[new_index] = self._feats[old_index]
            heads[new_index] = new_head
            deprels[new_index] = self._deprels[old_index]

        # Update.
        self.__init__(forms, lemmas, cpostags, postags, feats, heads, deprels)

    def delete(self, nodes):
        """
        Delete specified nodes from the tree.
        Lift the arcs of the orphaned nodes until their heads are non-deleted.
        """
        # Check indices.
        N = len(self)
        if not isinstance(nodes, (set, list, tuple)):
            nodes = [nodes]
        if not all(0 < node <= N for node in nodes):
            raise IndexError()

        # Reparent orphaned nodes.
        # Lift the arc until the parent is non-deleted node.
        # If all parents are deleted, we will hit the root eventually.
        deleted = set(nodes)
        alive_heads = [None] * N
        for node in range(1, N + 1):
            head = self.heads(node)
            while head in deleted:
                head = self.heads(head)
            alive_heads[node - 1] = head

        # Remap.
        new_nodes = {0: 0}
        new_node = 1

        for node in range(1, N + 1):
            if node in deleted:
                continue
            new_nodes[node] = new_node
            new_node += 1

        # Gather non-deleted stuff.
        forms = []
        lemmas = []
        cpostags = []
        postags = []
        feats = []
        heads = []
        deprels = []

        for node in range(1, N + 1):
            if node in deleted:
                continue
            forms.append(self.forms(node))
            lemmas.append(self.lemmas(node))
            cpostags.append(self.cpostags(node))
            postags.append(self.postags(node))
            feats.append(self.feats(node))
            heads.append(new_nodes[alive_heads[node - 1]])
            deprels.append(self.deprels(node))

        # Construct new tree.
        self.__init__(forms, lemmas, cpostags, postags, feats, heads, deprels)

    def set_head(self, node, head):
        """
        Make 'head' the head of the 'node'.
        If that breaks tree-ness (e.g. creates a cycle), raise ValueError.
        """
        # Check indices.
        if head in [node] + self.children_recursive(node):
            msg = 'future head %i is a (possibly indirect) child of %i'
            raise ValueError(msg % (head, node))
        if node <= 0 or head < 0:
            raise IndexError()

        # Set head.
        heads = self._heads[:]
        heads[node - 1] = head

        # Construct new tree.
        self.__init__(
            self._forms,
            self._lemmas,
            self._cpostags,
            self._postags,
            self._feats,
            heads,
            self._deprels
            )

    def append_copy(self, nodes):
        """
        Append a copy of gathered-together nodes at the end of the tree.
        For every node, preserve the parent unless the parent was copied too.
        """
        # Check indices.
        N = len(self)
        if not isinstance(nodes, (set, list, tuple)):
            nodes = [nodes]
        if not all(0 < node <= N for node in nodes):
            raise IndexError()

        # Determine where we want the new nodes.
        copied = sorted(nodes)
        new_nodes = {0: 0}
        new_node = N + 1
        for node in copied:
            new_nodes[node] = new_node
            new_node += 1

        # Prepare to append.
        forms = []
        lemmas = []
        cpostags = []
        postags = []
        feats = []
        heads = []
        deprels = []

        for node in copied:
            head = self.heads(node)
            if head in copied:
                head = new_nodes[head]

            forms.append(self.forms(node))
            lemmas.append(self.lemmas(node))
            cpostags.append(self.cpostags(node))
            postags.append(self.postags(node))
            feats.append(self.feats(node))
            heads.append(head)
            deprels.append(self.deprels(node))

        # Append.`
        self.append(forms, lemmas, cpostags, postags, feats, heads, deprels)

    BEFORE = '-'
    AFTER = '+'

    def move(self, nodes, anchor, where):
        """
        Move gathered-together nodes before or after the given anchor node.

        Moving nodes in a tree is basically a reordering.
        Return index remapping that would've been sufficient for reorder().
        (I.e. new_index_by_old_index).

        'anchor' can be either "-" (before) or "+" (after).
        """
        N = len(self)
        if not isinstance(nodes, (set, list, tuple)):
            nodes = [nodes]
        if not all(0 < node <= N for node in nodes):
            raise IndexError()

        # Compose a reordering.
        what = set(nodes)
        new_indices = [None] * N
        new_index = 0

        # Nodes up to, but not including, anchor.
        for node in range(1, anchor):
            if node in what:
                continue
            new_indices[node - 1] = new_index
            new_index += 1

        # Anchor (move after).
        if where == self.AFTER and anchor != 0:
            new_indices[anchor - 1] = new_index
            new_index += 1

        # New nodes.
        for node in sorted(what):
            if node != anchor:
                new_indices[node - 1] = new_index
                new_index += 1

        # Anchor (move before).
        if where == self.BEFORE and anchor != 0:
            new_indices[anchor - 1] = new_index
            new_index += 1

        # Nodes from anchor (not including) to the end.
        for node in range(anchor + 1, N + 1):
            if node in what:
                continue
            new_indices[node - 1] = new_index
            new_index += 1

        # Reorder.
        self.reorder(new_indices)
        return new_indices
