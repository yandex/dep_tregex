import copy
import re
import ply.lex
import ply.yacc

from dep_tregex.tree import *
from dep_tregex.tree_pattern import *
from dep_tregex.tree_action import *
from dep_tregex.tree_state import *

## ----------------------------------------------------------------------------
#                             Script application

class TreeScript:
    """
    A TreePattern object coupled with several TreeAction objects.
    """

    def __init__(self, pattern, actions):
        self.pattern = pattern
        self.actions = actions

def run_tree_scripts(tree, scripts):
    """
    Apply tree scripts in a specific manner.

    - Scripts are applied sequentially: first script several times, second
      script several times, etc.
    - Any given script is only applied to "original" nodes of the tree.
      "Original" nodes are nodes  that existed at the time that script was
      first run.
    - Script is applied to each "original" node only once.
    - Script is applied until there are no "original" nodes left, to which
      that script hasn't been applied.
    """
    backrefs_map = {}
    state = TreeState(copy.copy(tree), backrefs_map)

    for script in scripts:
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

            # Apply all actions.
            state.unmark(node)
            for action in script.actions:
                action.apply(state)

    return state.tree

## ----------------------------------------------------------------------------
#                              Script parser

class LexerError(ValueError):
    pass

class ParserError(ValueError):
    pass

class _TreeScriptParser:
    KEYWORDS = {
        'and': 'AND',
        'or': 'OR',
        'not': 'NOT',
        'is_top': 'IS_TOP',
        'is_leaf': 'IS_LEAF',
        'form': 'FORM',
        'lemma': 'LEMMA',
        'cpostag': 'CPOSTAG',
        'postag': 'POSTAG',
        'feats': 'FEATS',
        'deprel': 'DEPREL',
        'can_head': 'CAN_HEAD',
        'can_be_headed_by': 'CAN_BE_HEADED_BY',
        'copy': 'COPY',
        'move': 'MOVE',
        'delete': 'DELETE',
        'node': 'NODE',
        'group': 'GROUP',
        'before': 'BEFORE',
        'after': 'AFTER',
        'set': 'SET',
        'set_head': 'SET_HEAD',
        'try_set_head': 'TRY_SET_HEAD',
        'heads': 'HEADS',
        'headed_by': 'HEADED_BY'
        }

    TOKENS = [
        'ID',
        'STRING',
        'REGEX',
        'EQUALS',
        'COMMAND_SEP',
        'LPAREN',
        'RPAREN',
        'LBRACE',
        'RBRACE',
        'SEMICOLON',
        'BINARY_OP'
        ] + list(KEYWORDS.values())

    BINARY_OPS = {
        '.<--': HasLeftChild,
        '-->.': HasRightChild,
        '<--.': HasRightHead,
        '.-->': HasLeftHead,
        '.<-': HasAdjacentLeftChild,
        '->.': HasAdjacentRightChild,
        '<-.': HasAdjacentRightHead,
        '.->': HasAdjacentLeftHead,
        '>': HasChild,
        '>>': HasSuccessor,
        '<': HasHead,
        '<<': HasPredecessor,
        '$--': HasLeftNeighbor,
        '$++': HasRightNeighbor,
        '$-': HasAdjacentLeftNeighbor,
        '$+': HasAdjacentRightNeighbor
        }

    @classmethod
    def make_lexer(cls):
        tokens = cls.TOKENS
        t_ignore = ' '

        def track(t):
            # Compute position.
            start, end = t.lexer.lexmatch.span(0)
            line = t.lexer.lineno
            last_newline = t.lexer.lexdata.rfind(u'\n', 0, t.lexpos)
            col = (t.lexpos - last_newline)

            # Embed position into value.
            t.value = (t.value, (start, end, line, col))

        def t_ID(t):
            r'[_a-zA-Z][_a-zA-Z0-9]*'
            t.type = cls.KEYWORDS.get(t.value, 'ID')
            track(t)
            return t

        def t_STRING(t):
            r'"[^"]*"|' "'[^']*'"
            t.value = t.value[1:-1]
            track(t)
            return t

        def t_REGEX(t):
            r'/[^/]*/[ig]*'
            ignore_case = False
            anywhere = False
            while t.value[-1] in 'ig':
                if t.value[-1] == 'i':
                    ignore_case = True
                if t.value[-1] == 'g':
                    anywhere = True
                t.value = t.value[:-1]
            t.value = (t.value[1:-1], ignore_case, anywhere)
            track(t)
            return t

        def t_EQUALS(t):
            r'=='
            track(t)
            return t

        def t_BINARY_OP(t):
            track(t)
            return t
        binary_ops = sorted(cls.BINARY_OPS.keys(), key=len, reverse=True)
        t_BINARY_OP.__doc__ = '|'.join(map(re.escape, binary_ops))

        def t_COMMAND_SEP(t):
            r'::'
            track(t)
            return t

        def t_LPAREN(t):
            r'\('
            track(t)
            return t

        def t_RPAREN(t):
            r'\)'
            track(t)
            return t

        def t_LBRACE(t):
            r'\{'
            track(t)
            return t

        def t_RBRACE(t):
            r'\}'
            track(t)
            return t

        def t_SEMICOLON(t):
            r';'
            track(t)
            return t

        t_ignore_COMMENT = r'\#.*'

        def t_newline(t):
            r'\n+'
            t.lexer.lineno += len(t.value)

        def t_error(t):
            line = t.lexer.lineno
            last_newline = t.lexer.lexdata.rfind(u'\n', 0, t.lexpos)
            col = (t.lexpos - last_newline)
            c = t.value[0:1]
            msg = '(at line %i, col %i) invalid character %r' % (line, col, c)
            raise LexerError(msg)

        return ply.lex.lex()

    @classmethod
    def make_parser(cls, start):
        tokens = cls.TOKENS

        def untrack(p):
            s, pos = [None], [None]
            for i in range(1, len(p)):
                s.append(p[i][0])
                pos.append(p[i][1])

            known_pos = filter(bool, pos)
            if not known_pos:
                p0_pos = None
            else:
                start_0, end_0, line_0, col_0 = known_pos[0]
                start_n, end_n, line_n, col_n = known_pos[-1]
                p0_pos = (start_0, end_n, line_0, col_0)
            pos[0] = p0_pos

            return s, pos

        def track(p, pos):
            p[0] = (p[0], pos[0])

        def p_error(p):
            if p:
                start, end, line, col = p.value[1]
                val = p.value[0]
                msg = '(at line %i, col %i) unexpected token %r' % \
                    (line, col, val)
            else:
                msg = 'unexpected end of file'
            raise ParserError(msg)

        def p_tree_scripts(p):
            """
            tree_scripts :
                         | tree_script tree_scripts
            """
            s, pos = untrack(p)
            if len(p) == 1:
                p[0] = []
            else:
                p[0] = [s[1]] + s[2]
            track(p, pos)

        def p_tree_pattern(p):
            """
            tree_pattern : ID
                         | ID condition
                         | LPAREN tree_pattern RPAREN
            """
            s, pos = untrack(p)
            if len(p) == 2:
                p[0] = SetBackref(s[1], NotRoot(AlwaysTrue()))
            elif len(p) == 3:
                p[0] = SetBackref(s[1], NotRoot(s[2]))
            elif len(p) == 4:
                p[0] = s[2]
            p[0].pos = pos[0]
            track(p, pos)

        def p_tree_script(p):
            """
            tree_script : LBRACE tree_pattern COMMAND_SEP actions RBRACE
            """
            s, pos = untrack(p)
            p[0] = TreeScript(s[2], s[4])
            p[0].pos = pos[0]
            track(p, pos)

        def p_actions(p):
            """
            actions :
                    | action SEMICOLON actions
            """
            s, pos = untrack(p)
            if len(p) == 1:
                p[0] = []
            else:
                s[1].pos = pos[1]
                p[0] = [s[1]] + s[3]
            track(p, pos)

        def p_condition(p):
            """
            condition : condition_or
            """
            s, pos = untrack(p)
            p[0] = s[1]
            track(p, pos)

        def p_condition_or(p):
            """
            condition_or : condition_and or_conditions
            """
            s, pos = untrack(p)
            condition_and = s[1]
            or_conditions = s[2]

            if not or_conditions:
                p[0] = condition_and
            else:
                p[0] = Or([condition_and] + or_conditions)
            track(p, pos)

        def p_or_conditions(p):
            """
            or_conditions :
                          | OR condition_and or_conditions
            """
            s, pos = untrack(p)
            if len(p) == 1:
                p[0] = []
            else:
                p[0] = [s[2]] + s[3]
            track(p, pos)

        def p_condition_and(p):
            """
            condition_and : condition_not and_conditions
            """
            s, pos = untrack(p)
            condition_not = s[1]
            and_conditions = s[2]

            if not and_conditions:
                p[0] = condition_not
            else:
                p[0] = And([condition_not] + and_conditions)
            track(p, pos)

        def p_and_conditions(p):
            """
            and_conditions :
                           | AND condition_not and_conditions
            """
            s, pos = untrack(p)
            if len(p) == 1:
                p[0] = []
            else:
                p[0] = [s[2]] + s[3]
            track(p, pos)

        def p_condition_not(p):
            """
            condition_not : condition_op
                          | NOT condition_op
            """
            s, pos = untrack(p)
            if len(p) == 2:
                p[0] = s[1]
            else:
                p[0] = Not(s[2])
            track(p, pos)

        def p_condition_op_parens(p):
            """
            condition_op : LPAREN condition RPAREN
            """
            s, pos = untrack(p)
            p[0] = s[2]
            track(p, pos)

        def p_condition_op_binary(p):
            """
            condition_op : BINARY_OP tree_pattern
            """
            s, pos = untrack(p)
            p[0] = cls.BINARY_OPS[s[1]](s[2])
            track(p, pos)

        def p_condition_op_equals(p):
            """
            condition_op : EQUALS ID
            """
            s, pos = untrack(p)
            p[0] = EqualsBackref(s[2])
            track(p, pos)

        def p_condition_op_attr(p):
            """
            condition_op : attr string_condition
            """
            s, pos = untrack(p)
            if s[1] == 'feats':
                p[0] = FeatsMatch(pred_fn=s[2])
            else:
                p[0] = AttrMatches(attr=s[1], pred_fn=s[2])
            track(p, pos)

        def p_condition_op_is_top(p):
            """
            condition_op : IS_TOP
            """
            s, pos = untrack(p)
            p[0] = IsTop()
            track(p, pos)

        def p_condition_op_is_leaf(p):
            """
            condition_op : IS_LEAF
            """
            s, pos = untrack(p)
            p[0] = IsLeaf()
            track(p, pos)

        def p_condition_op_can_head(p):
            """
            condition_op : CAN_HEAD ID
            """
            s, pos = untrack(p)
            p[0] = CanHead(s[2])
            track(p, pos)

        def p_condition_op_can_be_headed_by(p):
            """
            condition_op : CAN_BE_HEADED_BY ID
            """
            s, pos = untrack(p)
            p[0] = CanBeHeadedBy(s[2])
            track(p, pos)

        def p_action_copy_move(p):
            """
            action : COPY selector ID where selector ID
                   | MOVE selector ID where selector ID
            """
            s, pos = untrack(p)
            kwargs = {
                'what': s[3],
                'sel_what': s[2],
                'where': s[4],
                'anchor': s[6],
                'sel_anchor': s[5]
                }

            if s[1] == 'copy':
                p[0] = Copy(**kwargs)
            else:
                p[0] = Move(**kwargs)
            track(p, pos)

        def p_action_delete(p):
            """
            action : DELETE selector ID
            """
            s, pos = untrack(p)
            p[0] = Delete(what=s[3], sel_what=s[2])
            track(p, pos)

        def p_action_set(p):
            """
            action : SET attr ID STRING
            """
            s, pos = untrack(p)
            if s[2] == 'feats':
                newval = s[4].split(u'|')
            else:
                newval = s[4]
            newval_fn = lambda x, newval=newval: newval
            p[0] = MutateAttr(s[3], '_' + s[2], newval_fn)
            track(p, pos)

        def p_action_set_head(p):
            """
            action : SET_HEAD     ID HEADED_BY ID
                   | SET_HEAD     ID HEADS     ID
                   | TRY_SET_HEAD ID HEADED_BY ID
                   | TRY_SET_HEAD ID HEADS     ID
            """
            s, pos = untrack(p)
            raise_ = (s[1] == 'set_head')
            if s[3] == 'headed_by':
                node, head = s[2], s[4]
            else:
                node, head = s[4], s[2]
            p[0] = SetHead(node=node, head=head, raise_on_invalid_head=raise_)
            track(p, pos)

        def p_action_group(p):
            """
            action : GROUP ID ID
            """
            s, pos = untrack(p)
            p[0] = GroupTogether(s[2], s[3])
            track(p, pos)

        def p_attr(p):
            """
            attr : FORM
                 | LEMMA
                 | CPOSTAG
                 | POSTAG
                 | FEATS
                 | DEPREL
            """
            s, pos = untrack(p)
            p[0] = {
                'form': 'forms',
                'lemma': 'lemmas',
                'cpostag': 'cpostags',
                'postag': 'postags',
                'feats': 'feats',
                'deprel': 'deprels'
                }[s[1]]
            track(p, pos)

        def p_string_condition_str(p):
            """
            string_condition : STRING
            """
            s, pos = untrack(p)
            p[0] = lambda x, string=s[1]: x == string
            track(p, pos)

        def p_string_condition_regex(p):
            """
            string_condition : REGEX
            """
            s, pos = untrack(p)
            pattern, ignore_case, anywhere = s[1]
            r = compile_regex(pattern, ignore_case, anywhere)
            p[0] = lambda x, r=r: r.search(x)
            track(p, pos)

        def p_selector(p):
            """
            selector : NODE
                     | GROUP
            """
            s, pos = untrack(p)
            if s[1] == 'node':
                p[0] = NODE
            else:
                p[0] = GROUP
            track(p, pos)

        def p_where(p):
            """
            where : BEFORE
                  | AFTER
            """
            s, pos = untrack(p)
            if s[1] == 'before':
                p[0] = Tree.BEFORE
            else:
                p[0] = Tree.AFTER
            track(p, pos)

        return ply.yacc.yacc(
            debug=0,
            write_tables=0,
            errorlog=ply.yacc.NullLogger()
            )

    def __init__(self, start):
        self.lexer = self.make_lexer()
        self.parser = self.make_parser(start)

    def parse(self, text):
        res, pos = self.parser.parse(text, lexer=self.lexer)
        return res

_TREE_SCRIPT_PARSER = None
_TREE_PATTERN_PARSER = None

def parse_pattern(text):
    """
    Parse a text, contatining a single tree pattern.
    Return TreePattern object.
    """

    # Compile parser on-demand.
    global _TREE_PATTERN_PARSER
    if _TREE_PATTERN_PARSER is None:
        _TREE_PATTERN_PARSER = _TreeScriptParser(start='tree_pattern')

    # Parse.
    return _TREE_PATTERN_PARSER.parse(text)

def parse_scripts(text):
    """
    Parse a text, contatining several tree scripts.
    Return list of TreeScript objects.
    """

    global _TREE_SCRIPT_PARSER
    if _TREE_SCRIPT_PARSER is None:
        _TREE_SCRIPT_PARSER = _TreeScriptParser(start='tree_scripts')

    # Parse.
    scripts = _TREE_SCRIPT_PARSER.parse(text)

    # Augment scripts, patterns and actions with their text.
    for script in scripts:
        # Augment script.
        start, end, line, col = script.pos
        script.text = text[start:end]

        # Augment pattern.
        start, end, line, col = script.pattern.pos
        script.pattern.text = text[start:end]

        # Augment actions.
        for action in script.actions:
            start, end, line, col = action.pos
            action.text = text[start:end]

    return scripts
