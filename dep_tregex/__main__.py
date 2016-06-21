from __future__ import print_function

import argparse
import cgi
import codecs
import collections
import random
import sys
import tempfile
import webbrowser

from dep_tregex.conll import *
from dep_tregex.tree_script import *
from dep_tregex.tree_to_html import *

## ----------------------------------------------------------------------------
#                                  Actions

# - Extract words - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

def words():
    for tree in read_trees_conll(sys.stdin):
        forms = [tree.forms(i) for i in range(1, len(tree) + 1)]
        print(u' '.join(forms))

# - Count trees - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

def wc():
    num = 0
    for tree in read_trees_conll(sys.stdin):
        num += 1
    print(num)

# - N'th tree - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

def nth(num):
    trees_read = 0
    for i, tree in enumerate(read_trees_conll(sys.stdin)):
        if i + 1 == num:
            write_tree_conll(sys.stdout, tree)

# - Head  - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

def head(num):
    for i, tree in enumerate(read_trees_conll(sys.stdin)):
        if i < num:
            write_tree_conll(sys.stdout, tree)

# - Tail  - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

def tail(num):
    queue = collections.deque([], maxlen=num)
    for i, tree in enumerate(read_trees_conll(sys.stdin)):
        if len(queue) == num:
            queue.popleft()
        queue.append(tree)

    for tree in queue:
        write_tree_conll(sys.stdout, tree)

# - Not head  - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

def not_head(num):
    """
    Print trees N, N+1, etc. (indices 1-based).
    """
    for i, tree in enumerate(read_trees_conll(sys.stdin)):
        if i + 1 >= num:
            write_tree_conll(sys.stdout, tree)

# - Shuffle - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

def shuf():
    trees = list(read_trees_conll(sys.stdin))
    random.shuffle(trees)
    for tree in trees:
        write_tree_conll(sys.stdout, tree)

# - HTML  - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

_HL_LIMIT = 100
_HL_LIMIT_MSG = 'Too many trees; #%i and on will not be highlighted on hover.'
_LIMIT_MSG = 'Printing only %i trees; override with --limit'

def _html(limit, fields, file):
    """
    Print trees from stdin and write HTML to 'file'.

    limit: maximal number of trees to print
    fields: CoNLL fields to print in trees
    file: file to write HTML to
    """
    write_prologue_html(file)

    for i, tree in enumerate(read_trees_conll(sys.stdin)):
        # Respect the limits.
        if i == limit:
            print(_LIMIT_MSG % i, file=sys.stderr)
        if i >= limit:
            continue
        if i == _HL_LIMIT:
            print(_HL_LIMIT_MSG % i, file=sys.stderr)

        # Draw.
        static = i >= _HL_LIMIT
        write_tree_html(file, tree, fields, [], static)

    write_epilogue_html(file)

def html(limit, fields, view, new):
    # If need not view in browser, write HTML to stdout.
    if not view:
        _html(limit, fields, file=sys.stdout)
        return

    # Create temporary file.
    f = tempfile.NamedTemporaryFile(delete=False, suffix='.html')
    filename = f.name
    f.close()

    # Write HTML to temporary file.
    with codecs.open(filename, 'wb', encoding='utf-8') as f:
        _html(limit, fields, file=f)

    # Open that file.
    webbrowser.open('file://' + filename, new=new*2)

# - Grep  - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

def _grep_text(pattern):
    """
    Read trees from stdin and print those who match the pattern.
    """
    # Parse pattern.
    pattern = parse_pattern(pattern)

    for tree in read_trees_conll(sys.stdin):
        # Match.
        match = False
        for node in range(1, len(tree) + 1):
            if pattern.match(tree, node, {}):
                match = True
                break

        # Print.
        if match:
            write_tree_conll(sys.stdout, tree)

def _grep_html(pattern, limit, fields, file):
    """
    Read trees from stdin, and print those who match the pattern as HTML,
    matched nodes highlighted.

    pattern: pattern to match against
    limit: maximal number of trees to print
    fields: CoNLL fields to print in trees
    file: file to write HTML to
    """
    # Parse pattern.
    pattern = parse_pattern(pattern)
    write_prologue_html(file)
    printed = 0

    for tree in read_trees_conll(sys.stdin):
        # Respect the limits.
        if printed == limit:
            print(_LIMIT_MSG % printed, file=sys.stderr)
            printed += 1
        if printed >= limit:
            continue
        if printed == _HL_LIMIT:
            print(_HL_LIMIT_MSG % printed, file=sys.stderr)

        # Match.
        matches = []
        for node in range(1, len(tree) + 1):
            if pattern.match(tree, node, {}):
                matches.append(node)

        # Draw.
        static = printed >= _HL_LIMIT
        if matches:
            write_tree_html(file, tree, fields, matches, static)
            printed += 1

    write_epilogue_html(file)

def grep(pattern, html, limit, fields, view, new):
    """
    Read trees from stdin and print those who match the pattern.
    If 'html' is False, print CoNLL trees.
    If 'html' is True and 'view' is False, print HTML to stdout.
    If 'html' is True and 'view' is True, view HTML in browser.
    """
    if not html:
        _grep_text(pattern)
        return

    if not view:
        _grep_html(pattern, limit, fields, file=sys.stdout)
        return

     # Create temporary file.
    f = tempfile.NamedTemporaryFile(delete=False, suffix='.html')
    filename = f.name
    f.close()

    # Write HTML to temporary file.
    with codecs.open(filename, 'wb', encoding='utf-8') as f:
        _grep_html(pattern, limit, fields, file=f)

    # Open that file.
    webbrowser.open('file://' + filename, new=new*2)

# - Sed - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

def sed(scripts_filename):
    # Read scripts.
    with open(scripts_filename, 'rt') as f:
        scripts = parse_scripts(f.read().decode('utf-8'))

    # Edit trees.
    for tree in read_trees_conll(sys.stdin):
        tree = run_tree_scripts(tree, scripts)
        write_tree_conll(sys.stdout, tree)

# - Gdb - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

_GDB_STYLES = """
    <style type="text/css">
      * { font-family: sans-serif; margin-top: 20px; margin-bottom: 20px; }
      body { margin-left: 30px; margin-top: -60px;}
      h1 { margin-top: 60px; }
      h2 { margin-top: 40px; }
      h2 { color: #444; font-style: italic; font-weight: normal; }

      pre {
        display: inline-block;
        font-family: monospace;
        margin: 0;
        padding: 5px 10px;
        background: #fafafa;
        border-radius: 5px;
      }

      .pos {
        margin-top: -20px;
        font-size: 90%%;
        color: #888;
      }

      h2 + .pos { font-style: italic; }
      pre + br + pre { margin-top: 10px; }
      h2.err { color: #e00; }
      pre.err { background-color: #e00; color: white; }
    </style>

"""

def _gdb_tree(scripts, scripts_text, tree, fields, file):
    """
    Debug-print a single tree transformation: visualize step-by-step script
    application as HTML and write to file.

    Don't write HTML prologue or epilogue.

    scripts: list of TreeScript
    scripts_text: text for 'scripts'
    tree: tree to apply scripts to
    fields: CoNLL fields to print in trees
    file: file to write HTML to
    """

    # Original tree.
    file.write(u'    <h1>Original tree</h1>\n')
    write_tree_html(file, tree, fields)

    # Whole script.
    file.write(u'    <h1>Whole script</h1>\n')
    file.write(u'<pre>%s</pre>\n' % cgi.escape(scripts_text))

    # Construct a tree state.
    backrefs_map = {}
    state = TreeState(tree, backrefs_map)
    exc = None

    # Apply scripts and log everything we can.
    for script_no, script in enumerate(scripts):
        # Reset the state
        state.unmark_all()
        for node in range(0, len(state.tree) + 1):
            state.mark(node)

        while True:
            backrefs_map.clear()

            # Find matching node.
            node = 0
            while node <= len(state.tree):
                if state.marked(node):
                    if script.pattern.match(state.tree, node, backrefs_map):
                        break
                node += 1

            # If no matching node, move on to the next script.
            if node == len(state.tree) + 1:
                break

            # Report the match.
            start, end, line, col = script.pos
            file.write(u'    <h1>Matched rule #%i</h1>' % (script_no + 1))
            file.write(u'    <div class="pos">(at line %i, col %i)</div>\n' %
                (line, col))
            file.write(u'<pre>%s</pre>\n' % cgi.escape(script.text))
            file.write(u'    <h2>Match</h2>\n')
            write_tree_html(file, tree, fields, [node])

            # Apply all actions and print tree after each step.
            state.unmark(node)
            for action_no, action in enumerate(script.actions):
                start, end, line, col = action.pos

                # Try to apply the action.
                try:
                    action.apply(state)
                except TreeActionError as e:
                    exc = e

                # If not succeeded, print the exception.
                if exc:
                    file.write(
                        u'    <h2 class="err">Error action #%i</h2>\n' %
                        (action_no + 1))
                    file.write(
                        u'    <div class="pos">(at line %i, col %i)</div>\n' %
                        (line, col))
                    file.write(u'<pre>%s</pre>\n' % cgi.escape(action.text))
                    file.write('<br>')
                    file.write(
                        u'<pre class="err">%s</pre>\n' %
                        cgi.escape(exc.msg))
                    break # Action loop.

                # Otherwise, print the tree.
                else:
                    file.write(
                        u'    <h2>After action #%i</h2>\n' %
                        (action_no + 1))
                    file.write(
                        u'    <div class="pos">(at line %i, col %i)</div>\n' %
                        (line, col))
                    file.write(u'<pre>%s</pre>\n' % cgi.escape(action.text))
                    write_tree_html(file, tree, fields)

            if exc:
                break # Node loop.

        if exc:
            break # Script loop.

    # Final tree.
    if not exc:
        file.write(u'    <h1>Final tree</h1>\n')
        write_tree_html(file, tree, fields)

def _gdb(scripts_filename, fields, file):
    """
    Debug-print trees from stdin and write HTML to 'file'.

    scripts_filename: path to scripts
    fields: CoNLL fields to print in trees
    file: file to write HTML to
    """

    # Read scripts.
    with open(scripts_filename, 'rt') as f:
        scripts_text = f.read().decode('utf-8')
        scripts = parse_scripts(scripts_text)

    # Debug a single tree.
    for tree in read_trees_conll(sys.stdin):
        write_prologue_html(file)
        file.write(_GDB_STYLES)
        _gdb_tree(scripts, scripts_text, tree, fields, file)
        write_epilogue_html(file)
        break

def gdb(scripts_filename, fields, view, new):
    """
    Debug-print trees from stdin and either write HTML to stdout or open in
    browser.

    scripts_filename: path to scripts
    fields: CoNLL fields to print in trees
    view: if True, open in browser, otherwise print HTML to stdout
    new: if True, don't try to reuse old browser tabs (when viewing)
    """

    # If need not view in browser, write HTML to stdout.
    if not view:
        _gdb(scripts_filename, fields, file=sys.stdout)
        return

    # Create temporary file.
    f = tempfile.NamedTemporaryFile(delete=False, suffix='.html')
    filename = f.name
    f.close()

    # Write HTML to temporary file.
    with codecs.open(filename, 'wb', encoding='utf-8') as f:
        _gdb(scripts_filename, fields, file=f)

    # Open that file.
    webbrowser.open('file://' + filename, new=new*2)

## ----------------------------------------------------------------------------
#                                  Main

if __name__ == '__main__':
    parser = argparse.ArgumentParser('python -mdep_tregex')
    subparsers = parser.add_subparsers(dest='cmd')

    def _add_html_arguments(p, limit=True):
        if limit:
            p.add_argument('--limit', help='draw only first N trees', type=int,
                           metavar='N', default=10)
        p.add_argument('--lemma', help='include LEMMA field',
                       action='store_true')
        p.add_argument('--cpostag', help='include CPOSTAG field',
                       action='store_true')
        p.add_argument('--postag', help='include POSTAG field',
                       action='store_true')
        p.add_argument('--feats', help='include FEATS field',
                       action='store_true')
        p.add_argument('--print', help="don't open in browser, print to stdout",
                       action='store_true')
        p.add_argument('--reuse-tab', help='reuse already opened browser tabs',
                        action='store_true')

    def _fields_from_args(args):
        fields = []
        if args.lemma:
            fields.append('lemma')
        if args.cpostag:
            fields.append('cpostag')
        if args.postag:
            fields.append('postag')
        if args.feats:
            fields.append('feats')
        return fields

    # Words
    words_p = subparsers.add_parser('words', help='extract words from tree')

    # Wc.
    wc_p = subparsers.add_parser('wc', help='count trees')

    # Nth
    nth_p = subparsers.add_parser('nth', help='print only Nth tree')
    nth_p.add_argument('N', help="print N'th tree (1-based)", type=int)

    # Head
    head_p = subparsers.add_parser('head', help='print only first N trees')
    head_p.add_argument('N', help='print first N trees (1-based)', type=int)

    # Tail
    tail_p = subparsers.add_parser('tail', help='print only last N trees')
    tail_p.add_argument('N', help='print last N trees (1-based)', type=str)

    # Shuffle.
    shuf_p = subparsers.add_parser('shuf', help='shuffle trees')

    # Grep.
    grep_p = subparsers.add_parser('grep', help='filter trees by pattern')
    grep_p.add_argument('PATTERN', help='dep-tregex pattern')
    grep_p.add_argument('--html', help='view matches in browser',
                        action='store_true')
    _add_html_arguments(grep_p)

    # Sed.
    sed_p = subparsers.add_parser('sed', help='apply tree scripts to trees')
    sed_p.add_argument('FILE', help='scripts file')

    # Html
    html_p = subparsers.add_parser('html', help='view trees in browser')
    _add_html_arguments(html_p)

    # Gdb.
    gdb_p = subparsers.add_parser('gdb', help='view step-by-step invocation')
    gdb_p.add_argument('FILE', help='scripts file')
    _add_html_arguments(gdb_p, limit=False)

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    # Print help when no arguments.
    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit(0)

    args = parser.parse_args()

    if args.cmd == 'words':
        words()

    elif args.cmd == 'wc':
        wc()

    elif args.cmd == 'nth':
        if args.N <= 0:
            nth_p.error('N has to be positive')
        nth(args.N)

    elif args.cmd == 'head':
        if args.N <= 0:
            head_p.error('N has to be positive')
        head(args.N)

    elif args.cmd == 'tail':
        try:
            n = int(args.N)
        except ValueError:
            tail_p.error('invalid integer N: %r' % args.N)
        if n <= 0:
            tail_p.error('N has to be positive')

        if args.N[0] != '+':
            tail(n)
        else:
            not_head(n)

    elif args.cmd == 'shuf':
        shuf()

    elif args.cmd == 'grep':
        fields = _fields_from_args(args)
        new = not args.reuse_tab
        grep(args.PATTERN, args.html, args.limit, fields, not args.print, new)

    elif args.cmd == 'sed':
        sed(args.FILE)

    elif args.cmd == 'html':
        if args.limit <= 0:
            html_p.error('--limit has to be positive')
        fields = _fields_from_args(args)
        html(args.limit, fields, not args.print, not args.reuse_tab)

    elif args.cmd == 'gdb':
        fields = _fields_from_args(args)
        gdb(args.FILE, fields, not args.print, not args.reuse_tab)
