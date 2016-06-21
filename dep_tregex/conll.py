from dep_tregex.tree import Tree

def _valid(text, empty_allowed=False):
    """
    Return whether field in a tree (FORM, LEMMA, etc.) can be written to
    a CoNLL file.
    """

    # Whitespace is not allowed inside strings.
    for c in u'\t\n ':
        if c in text:
            return False

    # Required field must not be empty.
    if not empty_allowed and not text:
        return False

    # Can't encode underscores: underscore means 'empty' in CoNLL format.
    if empty_allowed and text == u'_':
        return False

    return True

def read_trees_conll(filename_or_file, errors='strict'):
    """
    Read trees from CoNLL file and yield them one-by-one.

    filename_or_file: str or file object, where to read trees from.
    errors: how to handle unicode decode errors.
    """

    node = 1
    forms, lemmas, cpostags, postags, feats, heads, deprels = \
        [], [], [], [], [], [], []

    # Determine whether we have a filename or a file object.
    # If we have a filename, get a file object.
    file = filename_or_file
    if isinstance(file, str):
        file = open(file, rt)

    for line_no, line in enumerate(file):
        try:
            line = line.decode('utf-8', errors).strip(u'\n')

            # On empty line, yield the tree (if the tree is not empty).
            if not line:
                if forms:
                    tree = Tree(
                        forms, lemmas, cpostags, postags, feats, heads, deprels)
                    yield tree

                    node = 1
                    forms, lemmas, cpostags, postags, feats, heads, deprels = \
                        [], [], [], [], [], [], []
                continue

            # Split the line and check the format.
            parts = line.split(u'\t')
            if len(parts) != 10:
                msg = 'expected 10 tab-separated fields, got %i'
                raise ValueError(msg % len(parts))
            if parts[0] != unicode(node):
                msg = 'field 0: expected %r, got %r'
                raise ValueError(msg % (str(node), parts[0]))
            for i, part in enumerate(parts):
                if part:
                    continue
                msg = 'field %i: empty'
                raise ValueError(msg % i)

            # Parse the fields.
            node += 1
            form = parts[1]
            lemma = parts[2]
            cpostag = parts[3]
            postag = parts[4]
            feat = parts[5].split(u'|')
            head = int(parts[6])
            deprel = parts[7]

            if parts[2] == u'_':
                lemma = u''
            if parts[5] == u'_':
                feat = []

            # Append the fields to the current tree.
            forms.append(form)
            lemmas.append(lemma)
            cpostags.append(cpostag)
            postags.append(postag)
            feats.append(feat)
            heads.append(head)
            deprels.append(deprel)

        # Catch all exceptions occurred while parsing, and report filename
        # and line number.
        except ValueError, e:
            msg = 'error while reading CoNLL file %r, line %i: %s'
            raise ValueError(msg % (filename_or_file, line_no, e))

    # On end-of-file, don't forget to yield the last tree.
    if forms:
        yield Tree(forms, lemmas, cpostags, postagas, feats, heads, deprels)

def write_tree_conll(file, tree):
    """
    Write a tree to a file in CoNLL format.

    file: file-like object.
    tree: a Tree.
    """

    for i in range(len(tree)):
        node = i + 1
        form = tree.forms(node)
        lemma = tree.lemmas(node)
        cpostag = tree.cpostags(node)
        postag = tree.postags(node)
        feats = tree.feats(node)
        head = tree.heads(node)
        deprel = tree.deprels(node)

        if not _valid(form, empty_allowed=False):
            raise ValueError(u'invalid FORM: %r' % form)
        if not _valid(lemma, empty_allowed=True):
            raise ValueError(u'invalid LEMMA: %r' % lemma)
        if not _valid(cpostag, empty_allowed=False):
            raise ValueError(u'invalid CPOSTAG: %r' % cpostag)
        if not _valid(postag, empty_allowed=False):
            raise ValueError(u'invalid POSTAG: %r' % postag)
        if any(not _valid(feat, empty_allowed=False) for feat in feats):
            raise ValueError(u'invalid FEATS: %r' % feats)
        if not _valid(deprel, empty_allowed=False):
            raise ValueError(u'invalid DEPREL: %r' % deprel)

        id = unicode(node)
        lemma = lemma or u'_'
        head = unicode(head)
        feats = u'|'.join(feats) or u'_'

        parts = [id, form, lemma, cpostag, postag, feats, head, deprel]
        file.write(u'\t'.join(parts) + u'\t_\t_\n')

    file.write(u'\n')
