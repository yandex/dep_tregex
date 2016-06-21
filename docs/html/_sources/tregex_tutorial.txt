===============
Tregex tutorial
===============

**Tregexes** or **tree patterns** are tree-adapted regular expressions that
match *a single node* in a dependency tree and assign it a label. Using
assigned labels, **tree scripts** can modify the tree.

.. contents::
    :local:
    :depth: 1

Match-all
---------

An expression

.. code-block :: none

    w1

matches any node and marks it as ``w1`` (instead of ``w1`` we can use any
identifier). The marks can later be used in tree scripts to modify the tree
(we'll get there in a moment).

Logical operators
-----------------

After assigning an identifier to a node, we can write some conditions.

.. code-block :: none

    w1 form /.*[A-Z].*/ and cpostag "NN" and <--. w2

    #  ^^^^^^^^^^^^^^^^     ^^^^^^^^^^^^     ^^^^^^^
    #    condition 1         condition 2   condition 3

.. note:: Comments

    ``#`` can be used for comments in tree patterns and tree scripts.

This pattern matches tree nodes that satisfy three conditions:

- FORM has a capital letter
- Has "NN" CPOSTAG
- Has a head, that is located to the right, and that matches the pattern
  ``w2``. Since the pattern ``w2`` matches just any node, any head located to
  the right will do.

Neighborhood conditions
-----------------------

Note the last condition, ``w1 <--. w2``. It means "``w1`` must have a head to
the right, but the head also should match a pattern". Here, the pattern for the
head is just ``w2``, but we can write something more complex.

.. code-block:: none

    w1 <--. (w2 <--. w3)

    # or, equivalently

    w1 <--. w2 <--. w3

This pattern means "match a node, which has a head that lies to the right; this
head, in turn, should also have a head that lies to the right of it".

Why ``w1 <--. PATTERN`` stands for "has a head to the right that matches
``PATTERN``"? Note the little dot: it represents the node in the neighborhood,
which we are going to condition with a subpattern. On the dotless end of the
arrow is our initial node, which we were going to match in the first place.

.. code-block:: none

    (Visually)                    (Our metaphor)

    +-----------+                 w1 <--. PATTERN
    |           |
    v           |                 "Has a *head* to the *right*
    w1 ... <other node>            that matches PATTERN"



    +-----------+                 w1 -->. PATTERN
    |           |
    |           v                 "Has a *child* to the *right*
    w1 ... <other node>            that matches PATTERN"



         +-----------+            w1 .--> PATTERN
         |           |
         |           v            "Has a *head* to the *left*
    <other node> ... w1            that matches PATTERN"



         +-----------+            w1 .<-- PATTERN
         |           |            "Has a *child* to the *left*
         v           |             that matches PATTERN"
    <other node> ... w1


If the arrow is short, like ``.<-`` vs ``.<--``, this means that the node and
its head/child should be adjacent to each other, that there can be no nodes in
between.

You can almost imagine the tree from the pattern:

.. code-block:: none

    (Visually)                     (Our metaphor)

    +----------------+             w1 <--. w2 and -->. w3
    |                |
    |  +-----+       |             "Has a head to the right (w2) *and also* has
    v  |     v       |              a child to the right (w3)"
     w1  ...  w3 ...  w2

    +----------------+             w1 <--. w2 -->. w3
    |                |  +---+
    |                |  |   |      "Has a head to the right (w2) *that* has a
    v                |  |   v       child to the right (w3)"
     w1     ...       w2 ... w3

    +-------------------+          w1 <--. w2 .<-- w3
    |                   |
    |            +---+  |          "Has a head to the right (w2) that has a
    v            v   |  |          child to the *left* (w3)"
     w1        w3 ... w2


Strings & regular expressions
-----------------------------

Conditions like ``form`` or ``postag`` can either do an exact match
or a regular expression match.

.. code-block:: none

    n1 form 'cat'
    n1 form "dog"
    n1 form /cat|dog|catdog/

By default, regular expressions match the whole attribute (``/cat/`` won't
match "lolcat"), and also are case-sensitive. If you want substring match or
case sensitivity, use regex flags:

.. code-block:: none

    n1 form /cat/   # case-sensitive, whole-string    "cat"
    n1 form /cat/i  # case-insensitive, whole-string  "cat", "Cat", "CAT", ...
    n1 form /cat/g  # case-sensitive, substring       "cats", "lolcat", ...
    n1 form /cat/gi # case-insensitive, substring     "CAT", "Lolcat", ...

Backreferences
--------------

Suppose you want to match nodes on the left of their head which have a sibling
on the same side.

.. code-block:: none

    +----------+
    |          |
    |    +---+ |      a <--. c .<-- b
    v    v   | |
  >>a<<  b    c


This won't work the way you'd expect: most likely, the pattern will match with
``a`` and ``b`` assigned to the same node!

You need another condition that ``a`` and ``b`` should not be the same node;
backreferences come to the rescue.

.. code-block:: none

    a <--. (c .<-- (b not == a))
    #                     ^^^^--------- backreference match!

.. warning::

    There are severe restrictions on using backreferences. Please see the
    :ref:`description of node conditions <ref-node-conditions>`.

Scripts
-------

Now that you've mastered tree patterns, let's move on to the tree scripts.

Tree scripts modify the tree. Each script consists of a pattern, that assigns
backreferences, and of one or more actions.

.. code-block:: none

    # 1. Delete all "cat"s.

    {
        x form /cat/i
        ::
        delete node x;
    }

    # 2. Move all "dog"s to the beginning.

    {
        x form /dog/i $-- (start not $- w)
        ::
        move node x before node start;
    }

Pretty straighforward. Scripts are executed sequentially; each script is
applied once to each "original" node of the tree: the script is not applied to
the nodes created by it.

``move`` and ``copy`` actions
-----------------------------

Probably the most important actions are ``move`` and ``copy``.

.. code-block:: none

    (copy|move) (node|group) X (before|after) (node|group) Y

    e.g:

    copy node X before group Y
    move group X after group Y
    copy group X before node Y
    ...

Let's discuss one of them, e.g. ``move group X after node Y``.

First of all, ``group X`` means the action affects not only the node ``X`` but
also its "group": children, children of children, etc.
``move group X after node Y`` does the following:

- Gather X and, recursively, all children of X (its "group");
- Move gathered nodes right after the node Y, preserving initial order and
  heads.

.. code-block:: none

    +========+            (arc X => Y emphasized for clarity)
    | +--+   | +--+
    v |  v   | |  v
     X   x1   Y   y1
     ^^^^^^     ^--------- position right after Y
          |
          +--------------- X & children


    move group X after node Y:


             +---------------+
             |               |
             | +==+ +--+     |
             | |  v |  v     v
              Y    X   x1    y1
                   ^^^^^^

This also works for non-projective trees.

.. code-block:: none

    +================+
    |    +---------+ |
    | +--|----+    | |
    v |  v    v    | |
     X   y1   x1    Y
     ^^-------^^---------- X & children


    move group X after node Y:


         +---------+
         |         | +==+ +--+
         v         | |  v |  v
         y1         Y    X   x1

If you want to move (or copy) just the selected word, leaving its children where
they are, use ``node X`` instead of ``group X``.


.. code-block:: none

    +================+
    |    +---------+ |
    | +--|----+    | |
    v |  v    v    | |
     X   y1   x1    Y
     ^^       ^^--------- X's children
      +------------------ X


    move node X after node Y:

              +-----------+
         +----|----+      |
         |    |    | +==+ |
         v    v    | |  v |
         y1   x1    Y    X

``move ... after group Y`` moves after the last (leftmost) node of the group
of ``Y``. ``move ... before group Y`` moves to the position before the first
(rightmost) node of the group of ``Y``.

Grouping
========

``group X Y`` action creates a "virtual arc" from ``X`` to ``Y`` and from ``Y``
to ``X``. These arcs are not present in a tree, don't affect its connectivity
and acyclicity, don't participate in neighborhood conditions like ``X <--. Y``,
**but** they are traversed for the purpose of determining the *group* of a node.

.. code-block:: none

    group X y2

    +--------+
    |    +--+| +--+
    v    v  || |  v
     X   y2   Y   y1
     ^^^^^^     ^--------- position right after Y
          |
          +--------------- X & its group


    move group X after node Y:


             +---------------+
             |+--------+     |
             ||+--+    |     |
             |||  v    v     v
              Y   X   y2    y1
                  ^^^^^^

Formally, the group of a node ``X`` is the union of ``X``, all of the groups of
the children of ``X`` and all of the groups of the nodes, grouped with ``X``
via ``group X Y`` or ``group Y X`` operations.
