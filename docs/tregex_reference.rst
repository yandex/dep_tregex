================
Tregex reference
================

.. contents::
    :local:
    :depth: 1

Syntax
------

.. productionlist::
    S: `script`*
    script: '{' `pattern` '::' (`action` ';')* '}'
    pattern: ID [`condition`]
           : '(' `pattern` ')'
    condition: '-->.' `pattern`
             : '.<--' `pattern`
             : '.-->' `pattern`
             : '<--.' `pattern`
             : '->.'  `pattern`
             : '.<-'  `pattern`
             : '.->'  `pattern`
             : '<-.'  `pattern`
             : '>' `pattern`
             : '>>' `pattern`
             : '<' `pattern`
             : '<<' `pattern`
             : '$++'  `pattern`
             : '$--'  `pattern`
             : '$+'   `pattern`
             : '$-'   `pattern`
             : `attr` `string_cond`
             : 'is_top'
             : 'is_leaf'
             : 'can_head' ID
             : 'can_be_headed_by' ID
             : '==' ID
             : '(' `condition` ')'
             : 'not' `condition`
             : `condition` 'and' `condition`
             : `condition` 'or' `condition`
    string_cond: "STRING"
               : 'STRING'
               : /REGEX/i
               : /REGEX/g
               : /REGEX/ig
               : /REGEX/gi
    action: ('copy' | 'move') ('node' | 'group') ID ('before' | 'after') ('node' | 'group') ID
          : 'delete' ('node' | 'group') ID
          : 'set' `attr` ID STR
          : ('set_head' | 'try_set_head') ID ('headed_by' | 'heads') ID
          : 'group' ID ID
    attr: 'form'
        : 'lemma'
        : 'cpostag'
        : 'postag'
        : 'feats'
        : 'deprel'

Script application
------------------

Scripts consist of a sequence of patterns, each pattern paired with a list of
actions.

.. code-block:: none


    # 1. Delete all "cat"s.

    {
        x form /cat/i
        ::
        delete node x;
    }

    # 2. Copy all "dog"s to the beginning.

    {
        x form /dog/i $-- (start not $- w)
        ::
        copy node x before node start;
    }

Patterns and actions are separated by ``::``.

Steps of the script are applied sequentially: first ``#1`` several times,
then ``#2`` several times, etc.

On each step, a script is applied to every possible node of the tree *once*,
and not applied to the nodes created by the script itself.

An example:

.. code-block:: none

     +---------+
     |    +--+ | +--+
     |    v  | v |  v
    ROOT cat  and  dog

    # 1: pattern
    x node /cat/i

     +---------+
     |    +--+ | +--+
     |    v  | v |  v
    ROOT cat  and  dog
         {x}

    #1: actions
    delete node x

     +---------+
     |         | +--+
     |         v |  v
    ROOT      and  dog

    # 1: doesn't match
    # 2: pattern
    x node /dog/i $-- (start not $- w)

     +---------+
     |         | +--+
     |         v |  v
    ROOT      and  dog
            {start}{x}

    #2: actions
    copy node x before node start

     +---------+
     |    +--+ | +--+
     |    v  | v |  v
    ROOT dog  and  dog
        (new)     (old)

    # 2: doesn't match
    # - Node "dog" (new) was created by script #2, and scripts are not applied
    #   to nodes created by themselves.
    # - Node "dog" (old) was already matched by script #2.

    # Done.

.. _ref-node-conditions:

Node conditions
---------------

======================= =
``ATTR STR_COND``       Attribute matches :ref:`string condition <ref-string-conditions>`. Available attributes: ``form``, ``lemma``, ``cpostag``, ``postag``, ``feats``, ``deprel``.
``is_top``              Node's parent is the root
``is_leaf``             Node has no children
``can_head ID``         Whether the tree stays valid (connected & acyclic) if we attach a given :ref:`backreference <ref-backreferences>` to the node.
``can_be_headed_by ID`` If ``X can_be_headed_by Y`` matches whenever ``Y can_head X`` does.
``== ID``               Node matches a :ref:`backreference <ref-backreferences>`
======================= =

.. _ref-backreferences:

Backreferences
--------------

Backreference matches can only be made in subconditions of the pattern where
the reference was set. Like this:

.. code-block:: none

                          vvvv------ backreference match
    a <--. (c .<-- (b not == a))
    ^       ^^^^^^^^^^^^^^^^^^^----- subcondition of 'a'
    +------------------------------- reference setup of 'a'

This is wrong:

.. code-block:: none

                               vvvv--- BAD backreference match
    c .<-- (a) and .<-- (b not == a)
            ^^------------------------ 'a' has no subconditions
            |
            +------------------------- reference setup of 'a'

.. warning::

    If the backreference match is not in a subcondition, *the system might not
    raise an error*. Be careful.

.. _ref-string-conditions:

String conditions
-----------------

Node conditions like ``form`` or ``deprel`` can be used either to match the form
(or dependency relation) exactly, or with a regular expression.

.. code-block:: none

    n1 form 'cat'
    n1 form "dog"
    n1 form /dog|cat/

- Strings can be enclosed either in single ``'`` or double ``"`` quotes.
- Regular expressions use extended
  `PCRE syntax <http://www.pcre.org/current/doc/html/pcre2syntax.html>`_.
- Regular expressions are matched *to the whole string*. If you want
  a substring match, e.g. to match a word with a "ni" inside, write ``/ni/g``.
- Regular expressions are case-sensitive. Use ``/.../i`` for case-insensitive
  matching.
- Strings support *no escaping*. E.g. you can't write a single-quoted string
  with a single quote inside.
- In a similar fashion, regular expressions support no escaping of ``/``: you
  can't make a regular expression with ``/`` inside.
- Conditions on FEATS field work like this:

  1. Feats are printed as a string.

     .. code-block:: none

       Noun|Pnon|Nom|A3sg

  2. A `string condition <nlp.dep_parser-string_conditions>`_ is applied.

     .. code-block:: none

       w1 feats /Noun/g

Neighborhood conditions
-----------------------

============================== =
``-->.``                       Has a child to the right
``.<--``                       Has a child to the left
``.-->``                       Has a head to the left
``<--.``                       Has a head to the right
``->.``                        Has a child immediately to the right
``.<-``                        Has a child immediately to the left
``.->``                        Has a head immediately to the left
``<-.``                        Has a head immediately to the right
``>``                          Node has a child.
``<``                          Node has a parent.
``>>``                         Node has a descendant.
``<<``                         Node has an ancestor.
``$++``                        Has a neighbor to the right
``$--``                        Has a neighbor to the left
``$+``                         Has a neighbor immediately to the right
``$-``                         Has a neighbor immediately to the left
============================== =

Script actions
--------------

============================================================== =
``(move|copy) (node|group) ID (after|before) (node|group) ID`` Move or copy node (or the whole group) to given position
``delete (node|group) ID``                                     Delete a node (or the whole group)
``set ATTR ID STR``                                            Set node's attribute. Available attributes: ``form``, ``lemma``, ``cpostag``, ``postag``, ``feats``, ``deprel``
``set_head IDa (headed_by|heads) IDb``                         Set node's head (``IDb`` becomes the head of ``IDa`` if ``IDa headed_by IDb``, otherwise vice versa). *Fail* if tree becomes cyclic or disconnected
``try_set_head IDa headed_by IDb``                             Set node's head. *Do not fail* if tree becomes cyclic or disconnected
``group IDa IDb``                                              Consider ``IDa`` in a group of ``IDb`` and vice versa
============================================================== =

- ``group X Y`` creates virtual arcs from ``X`` to ``Y`` and from ``Y`` to
  ``X``, considered only for determining node's group in ``move``, ``copy``, and
  ``delete`` operations.
- The *group* of node ``X`` is ``X``, union of the *groups* of children of
  ``X``, and union of the *groups* of nodes ``n`` that were grouped with ``X``
  using ``group X n`` or ``group n X`` operation.
- ``move`` and ``copy`` actions can move either the node or the whole group.
  If the whole group is moved, all nodes from the group are gathered and put
  together into desired position, one node adjacent to the other, preserving
  initial relative order.
- ``move (node|group) Y after group X`` moves ``Y`` after the last node of
  ``X`` 's *group*. ``move (node|group) Y after group X`` moves ``Y`` before
  the first node of ``X`` 's *group*.
- ``move`` and ``copy`` actions can make the tree non-projective.
- ``set_head`` fails if the new head is (possibly indirect) child of the node
  we're trying to set head on. ``try_set_head`` does nothing in this case. The
  use of former is encouraged in development, latter -- in production.

Root node
---------

There is a special node in the tree, that binds it together: the ``ROOT`` node.

.. code-block:: none

     +-----------+
     |      +--+ | +--+
     |      v  | v |  v
    (ROOT) cat  and  dog

It is introduced for the tree to always be connected in case the tree
syntactically encodes more than one sentence.

.. code-block:: none

     +---------------------+
     |+----+               |
     ||    |+----+    +---+|
     ||    v|    v    v   |v
    (ROOT) cat   .   And  dog
           \_____/   \______/<--- Sentence 2
              ^------------------ Sentence 1

**The root node is never matched by any pattern**.

Operator priority
-----------------

============= =======
1 (highest)   ``not``
2             ``and``
3 (lowest)    ``or``
============= =======

Also, ``and`` and ``or`` append conditions to the innermost node, e.g.

.. code-block:: none

    a <--. b <--. c and .<-- d

Is equivalent to

.. code-block:: none

    a <--. (b <--. c and .<-- d)
              \____/     \____/ <----- Condition 2 on "b"
                 ^-------------------- Condition 1 on "b"

**NOT** to

.. code-block:: none

    a <--. (b <--. c) and (.<-- d)
      \_____________/     \______/ <-- Condition 2 on "a"
            ^------------------------- Condition 1 on "a"
