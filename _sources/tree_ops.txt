========================
Unix-like tree utilities
========================

All utilities read trees from stdin and write trees to stdout.

``words``
=========

Extract and print words from trees.

.. code-block:: none

    python -m'dep_tregex' words <en-ud-test.conllu

.. code-block:: none

    What if Google Morphed Into GoogleOS ?
    What if Google expanded on its search - engine ( and now e-mail ) wares into a full - fledged operating system ?
    [ via Microsoft Watch from Mary Jo Foley ]
    <...>


``wc``
======

Count number of trees.

.. code-block:: none

    python -m'dep_tregex' wc <en-ud-test.conllu

.. code-block:: none

    2077

``nth``
=======

Print N'th tree (N is 1-based).

.. code-block:: none

    python -m'dep_tregex' nth 10 <en-ud-test.conllu

.. code-block:: none

    1	I	I	PRON	PRP	Case=Nom|Number=Sing|Person=1|PronType=Prs	3	nsubj	_	_
    2	'm	be	AUX	VBP	Mood=Ind|Tense=Pres|VerbForm=Fin	3	aux	_	_
    3	staying	stay	VERB	VBG	Tense=Pres|VerbForm=Part	0	root	_	_
    4	away	away	ADV	RB	_	3	advmod	_	_
    5	from	from	ADP	IN	_	7	case	_	_
    6	the	the	DET	DT	Definite=Def|PronType=Art	7	det	_	_
    7	stock	stock	NOUN	NN	Number=Sing	4	nmod	_	_
    8	.	.	PUNCT	.	_	3	punct	_	_

``head``
========

Print first N trees.

.. code-block:: none

    python -m'dep_tregex' head 10 <en-ud-test.conllu

``tail``
========

Print last N trees.

.. code-block:: none

    python -m'dep_tregex' tail 10 <en-ud-test.conllu

Also supports ``tail +N`` syntax, which prints all but first N - 1 trees.

.. code-block:: none

    python -m'dep_tregex' tail +10 <en-ud-test.conllu

``shuf``
========

Randomly shuffle trees.

.. code-block:: none

    python -m'dep_tregex' shuf <en-ud-test.conllu

``html``
========

View trees in browser.

.. code-block:: none

    python -m'dep_tregex' html <en-ud-test.conllu

See also `Common HTML format options`_.

``grep``
========

Print only trees that match tregex pattern.

.. code-block:: none

    python -m'dep_tregex' grep "w1 form /..../" <en-ud-test.conllu

.. option:: --html

    View matches in browser instead of printing matching trees to stdout.

    See also `Common HTML format options`_.

``sed``
=======

Apply scripts from file to the trees and print resulting trees.

.. code-block:: none

    python -m'dep_tregex' sed script.txt <en-ud-test.conllu

``gdb``
=======

View step-by step script application (done by ``sed``) to a single tree.

.. code-block:: none

    python -m'dep_tregex' gdb script.txt <en-ud-test.conllu

See also `Common HTML format options`_.

Common HTML format options
==========================

Commands that print or show HTML (``html``, ``grep --html``, and ``gdb``)
have common formatting options.

.. option:: --print

    Instead of opening a browser window, print HTML to stdout.

.. option:: --limit N

    Show only first *N* trees.

    Not applicable to ``gdb``, which always shows only one tree.

.. option:: --lemma

    Show ``LEMMA`` CoNLL field.

.. option:: --cpostag

    Show ``CPOSTAG`` CoNLL field.

.. option:: --postag

    Show ``POSTAG`` CoNLL field.

.. option:: --feats

    Show ``FEATS`` CoNLL field.

.. option:: --reuse-tab

    When opening a new browser tab, try to re-use existing one.
