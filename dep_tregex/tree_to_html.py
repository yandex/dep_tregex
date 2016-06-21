from __future__ import print_function

import cgi
import sys
import math

## -----------------------------------------------------------------------------
#                                  Style

#                         ~ All sizes are in px. ~

_TRANSITION = '0.1s ease-out, stroke-dasharray 0.02s'
_BIG_FONT = 12                   # Font for words.
_SMALL_FONT = 10                 # Font for deprels, lemmas, etc.
_SMALL_LINE = _SMALL_FONT * 1.33 # Line height for small font.
_ANGLE = math.pi / 3.            # Angle at which the arc enters the word.
_ARROW_SPREAD = math.pi / 12.    # Angular width of an arrow tip.
_ARROW_SIZE = _SMALL_FONT * .75  # Linear size of an arrow tip.
_ARROW_SIZE_MIDDLE = _ARROW_SIZE * .85 # (see picture)
_ARC_WIDTH = 0.5                # Arc line width.

#                       ~ An arrow looks like this ~
#                                             _
#                                         __--
#                    __\              __--
#       arrow    __--   \         __--   ++
#        sz  __--        \    __--         ++
#        __--             \ --              ++
#     \--                 o                  ++ ----- arrow spread
#      \              oooo                    ++          angle
#       \         ooooooo                     ++
#        \    oooooooooo______________________++__________________v____
#         ooooooooooooo __________________________________________|____
#         |   oooooooo|o                                          ^
#         |       oooo|oo                                         |
#         |           |ooo                                    arc width
#         |           |   o
#         |<--------->|
#           middle sz

# Height of a "flight level" for arcs.
_ARC_HEIGHT_UNIT = _SMALL_FONT * 1.2

# Horizontal distance between endpoint of an incoming arc
# and starting point of an outgoing arc of the same word.
_PORT_OFFSET = _BIG_FONT / 2.

_COLOR_BIG      = '#000' # Color for inactive big text.
_COLOR_BIG_H0   = '#888' # Very dim highlight color for big text.
_COLOR_BIG_H1   = '#c00' # Dim highlight color for big text.
_COLOR_BIG_H2   = '#f00' # Bright highlight color for big text.
_COLOR_BIG_HU   = '#08c' # User-highlighted big text.
_COLOR_SMALL    = '#444' # Color for incative small text.
_COLOR_SMALL_H0 = '#666' # Very dim highlight color for small text.
_COLOR_SMALL_H1 = '#800' # Dim highlight color for small text.
_COLOR_SMALL_H2 = '#900' # Bright highlight color for small text
_COLOR_SMALL_HU = '#048' # User-highlighted small text.

# SVG-wide stylesheet.
_STYLE = u"""\
    <style type="text/css">
      /* Generic */
      * { stroke: none; fill: none; transition: %s; }
      text { font-family: sans-serif; text-anchor: middle; cursor: default; }
      .hid { opacity: 0.0; }
      rect.hid { fill: #000; stroke: #000; stroke-width: %.2fpx; }
      path.hid { fill: none; stroke: #000; stroke-width: %.2fpx; }

      /* Labels & arcs */
      .big { font-size: %ipx; fill: %s; font-weight: bold; }
      .small { font-size: %ipx; fill: %s; }
      .user-hl > .big   { fill: %s; }
      .user-hl > .small { fill: %s; }
      .role { font-size: %ipx; fill: %s; font-style: italic; }
      .arc { stroke: black; stroke-width: %.2fpx; }
      .arrow { fill: %s; }

      /* Label and arc highlight on hover */
      g:hover > text.big { fill: %s; }
      g:hover > text.small { fill: %s; }
      g:hover > text.role { fill: %s; }
      g:hover > path.arc { stroke: %s; }
      g:hover > path.arrow { fill: %s; }

      /* Arc highlight on label hover */
      g:hover + g > text.role { fill: %s; }
      g:hover + g > path.arc { stroke: %s; stroke-dasharray: 5,5; }
      g:hover + g > path.arrow { fill: %s; }
    </style>""" % (
    _TRANSITION, _SMALL_FONT, _SMALL_FONT,            # Generic
    _BIG_FONT, _COLOR_BIG, _SMALL_FONT, _COLOR_SMALL, # .big, .small
    _COLOR_BIG_HU, _COLOR_SMALL_HU,                   # .user-hl
    _SMALL_FONT, _COLOR_SMALL,                        # .role
    _ARC_WIDTH, _COLOR_BIG,                           # .arc
                                                      # Label highlight
    _COLOR_BIG_H2, _COLOR_SMALL_H2, _COLOR_BIG_H2, _COLOR_BIG_H2, _COLOR_BIG_H2,
    _COLOR_BIG_H2, _COLOR_BIG_H2, _COLOR_BIG_H2       # Arc hover
    )

_PROLOGUE_HTML = u"""\
<!DOCTYPE html>
<html>
  <head>
    <meta charset="utf-8">
    <style type="text/css">
        svg { display: block; }
    </style>
    %s
  </head>
  <body>
""" % _STYLE

_EPILOGUE_HTML = u"""\
  </body>
</html>
"""

# Styles that are applied to a tree node when its immediate head is
# hovered over.
_HEAD_HOVER_STYLES = [
    u'.w%%i > text.big { fill: %s; }' % (_COLOR_BIG_H1,),
    u'.w%%i > text.small { fill: %s; }' % (_COLOR_SMALL_H1,),
    u'.a%%i > text.role { fill: %s; }' % (_COLOR_BIG_H1,),
    u'.a%%i > path.arc { stroke: %s; }' % (_COLOR_BIG_H1,),
    u'.a%%i > path.arrow { fill: %s; }' % (_COLOR_BIG_H1,)
    ]

# Styles that are applied to a tree node when its parent is hovered over,
_PARENT_HOVER_STYLES = [
    u'.w%%i > text.big { fill: %s; }' % (_COLOR_BIG_H0,),
    u'.w%%i > text.small { fill: %s; }' % (_COLOR_SMALL_H0,),
    u'.a%%i > text.role { fill: %s; }' % (_COLOR_BIG_H0,),
    u'.a%%i > path.arc { stroke: %s; }' % (_COLOR_BIG_H0,),
    u'.a%%i > path.arrow { fill: %s; }' % (_COLOR_BIG_H0,)
    ]

## -----------------------------------------------------------------------------
#                                 Utilities

def _label(tree, node, fields):
    """
    Compose a label for i'th word of a tree, according to 'fields'.
    Return a string (possibly multiline).
    """
    # Form (always).
    label = tree.forms(node)

    # Lemma.
    if 'lemma' in fields:
        label += u'\n' + tree.lemmas(node)

    # Postags.
    postags = []
    if 'cpostag' in fields:
        postags.append(tree.cpostags(node))
    if 'postag' in fields:
        postags.append(tree.postags(node))
    if postags:
        label += u'\n' + u'/'.join(postags)

    # Features.
    if 'feats' in fields:
        label += u'\n' + u'|'.join(tree.feats(node))

    return cgi.escape(label)

def _label_height(text):
    """
    Return label text height.
    First line is in big font, other lines are in small font.
    """
    return _BIG_FONT + _SMALL_LINE * text.count(u'\n')

def _label_width(text):
    """
    Return label text width.
    Width of a single glyph is considered to be equal to font size.
    First line is in big font, other lines are in small font.
    """
    width = 0
    for lineno, line in enumerate(text.split(u'\n')):
        size = [_BIG_FONT, _SMALL_FONT][lineno > 0] # Cool idiom, huh?
        width = max(width, size * len(line))
    return width

#    ~ Arcs are composed of two circular segments and a straight line. ~
#               Segments touch the word at a specific angle.

def _arc_radius(height_in_units):
    """
    Return radius of a circular segment of an arc of a given height level.
    """
    return height_in_units * _ARC_HEIGHT_UNIT / (1 - math.cos(_ANGLE))

def _arc_min_length(height_in_units):
    """
    Return minimal horizontal size for an arc of a given "flight level".
    """
    return 2 * _arc_radius(height_in_units) * math.sin(_ANGLE)

def _parent_arc_start_offset(tree, node):
    head = tree.heads(node)
    head_head = tree.heads(head)

    projective = (
        (head_head < head < node) or
        (node < head < head_head) or
        (head_head < node < head) or
        (head < node < head_head)
        )

    if projective:
        if node < head:
            return -_PORT_OFFSET
        else:
            return +_PORT_OFFSET
    else:
        if head_head < head:
            return +_PORT_OFFSET
        else:
            return -_PORT_OFFSET

def _draw_label(file, text, x, y, css_class):
    """
    Draw a multiline label at given position.
    Enclose elements in a <g class="...">.
    """
    width = _label_width(text)
    height = _label_height(text)

    # Start a group.
    file.write(u'      <g class="%s">\n' % css_class)

    # Invisible hover-rectangle.
    # Makes it easier to hover over the label.
    file.write(u'        <rect x="%i" y="%i" width="%i" height="%i" class="hid" />\n' %
        (x - width / 2, y, width, height))

    # Lines of text.
    y += _BIG_FONT
    for lineno, line in enumerate(text.split(u'\n')):
        file.write(u'        <text x="%i" y="%i" class="%s">%s</text>\n' %
            (x, y, 'big' if lineno == 0 else 'small', line))
        y += _SMALL_LINE

    # End a group.
    file.write(u'      </g>\n')

def _draw_root_arc(file, x, y, height_in_units, deprel, css_class):
    """
    Draw a vertical "arc from the root" to the node at (x, y).
    Enclose elements in a <g class="...">.
    """
    height = height_in_units * _ARC_HEIGHT_UNIT

    # Start.
    file.write(u'      <g class="%s">\n' % css_class)

    # Path.
    path = 'M %i %i L %i %i' % (x, y, x, y - height)
    file.write(u'        <path d="%s" class="arc" />\n' % path)
    file.write(u'        <path d="%s" class="arc hid" />\n' % path)

    # Arrow.
    _draw_arrow(file, x, y, math.pi / 2)

    # Role.
    deprel = cgi.escape(deprel)
    file.write(u'        <text x="%i" y="%i" class="role">%s</text>\n' %
        (x, y - height - 0.2 * _SMALL_FONT, deprel))

    # End.
    file.write(u'      </g>\n')

def _draw_arc(file, start_x, end_x, y, height_in_units, deprel, css_class):
    """
    Draw an arc from the node at (start_x, y) to the node at (end_x, y).
    Enclose elements in a <g class="...">.
    """
    height = height_in_units * _ARC_HEIGHT_UNIT
    radius = _arc_radius(height_in_units)
    length = _arc_min_length(height_in_units)

    # Start.
    file.write(u'      <g class="%s">\n' % css_class)

    # Path.
    path = (
        'M %.2f %.2f'
        'A %.2f %.2f 0 0 1 %.2f %.2f'
        'L %.2f %.2f'
        'A %.2f %.2f 0 0 1 %.2f %.2f'
        ) % (
        min(start_x, end_x), y,
        radius, radius, min(start_x, end_x) + length / 2, y - height,
        max(start_x, end_x) - length / 2, y - height,
        radius, radius, max(start_x, end_x), y
        )
    file.write(u'        <path d="%s" class="arc" />\n' % path)
    file.write(u'        <path d="%s" class="arc hid" />\n' % path)

    # Arrow.
    arrow_angle = _ANGLE if start_x > end_x else math.pi - _ANGLE
    _draw_arrow(file, end_x, y, arrow_angle)

    # Role.
    deprel = cgi.escape(deprel)
    file.write(u'        <text x="%i" y="%i" class="role">%s</text>\n' %
        ((start_x + end_x) / 2, y - height - 0.2 * _SMALL_FONT, deprel))

    # End.
    file.write(u'      </g>\n')

def _draw_arrow(file, tip_x, tip_y, angle):
    """
    Draw an arrow with a tip at (tip_x, tip_y), "attacking" the surface at a
    given angle.
    """
    # Offset the tip.
    tip_x -= _ARROW_SIZE * 0.2 * math.cos(angle)
    tip_y += _ARROW_SIZE * 0.2 * math.sin(angle)

    # Draw the arrow.
    path = (
        'M %.2f %.2f'
        'L %.2f %.2f'
        'L %.2f %.2f'
        'L %.2f %.2f'
        'Z'
        ) % (
        tip_x, tip_y,
        tip_x + _ARROW_SIZE * math.cos(angle - _ARROW_SPREAD),
        tip_y - _ARROW_SIZE * math.sin(angle - _ARROW_SPREAD),
        tip_x + _ARROW_SIZE_MIDDLE * math.cos(angle),
        tip_y - _ARROW_SIZE_MIDDLE * math.sin(angle),
        tip_x + _ARROW_SIZE * math.cos(angle + _ARROW_SPREAD),
        tip_y - _ARROW_SIZE * math.sin(angle + _ARROW_SPREAD),
        )
    file.write(u'        <path d="%s" class="arrow"/>\n' % (path,))

## -----------------------------------------------------------------------------
#                                   Main

def write_prologue_html(file):
    file.write(_PROLOGUE_HTML)

_UID = 0

def write_tree_html(file, tree, fields=[], highlight_nodes=[], static=False):
    N = len(tree)
    if N == 0:
        return

    # Collect all tree arcs.
    arcs = [(node, tree.heads(node)) for node in range(1, N + 1)]
    arc_length = lambda arc: abs(arc[0] - arc[1])

    # Determine height of every arc: 1, 2, 3, etc.
    # At each position, track the occupied flight levels.
    arc_heights = [0] * N
    occupied = [set() for i in range(N)]

    # Assign lower levels to arcs sequentially, starting from shorter arcs.
    for arc in sorted(arcs, key=arc_length):
        node, head = arc
        start, end = min(arc) - 1, max(arc)

        # Skip arcs from the root (they go vertically).
        if head == 0:
            continue

        # Determine the occupied flight levels below arc.
        positions = occupied[start+1:end-1] + [set()]
        occupied_below_arc = set.union(*positions)

        # Find the first available flight level.
        level = 1
        while level in occupied_below_arc:
            level += 1

        # Remember the height of the arc.
        arc_heights[node - 1] = level
        for pos in range(start, end):
            occupied[pos].add(level)

    # Assign height for root arcs.
    root_height = max(arc_heights) + 1
    for i in range(N):
        if arc_heights[i] == 0:
            arc_heights[i] = root_height

    # Get and measure labels.
    labels = [_label(tree, node, fields) for node in range(1, N + 1)]
    label_widths = map(_label_width, labels)
    label_heights = map(_label_height, labels)

    # Determine words' centers.
    centers = []
    start = _BIG_FONT
    for width in label_widths:
        centers.append(start + width / 2)
        start += width + _BIG_FONT

    # Shift words' centers to accomodate arcs.
    for node, head in arcs:
        if head == 0:
            continue

        # Compute real margin and minimal required margin.
        start, end = sorted((node, head))
        margin = centers[end - 1] - centers[start - 1] - 2 * _PORT_OFFSET
        min_margin = _arc_min_length(arc_heights[node - 1])

        # Shift words to the right.
        if margin < min_margin:
            for i in range(end - 1, len(centers)):
                centers[i] += min_margin - margin

    # Compute width and height.
    baseline = _BIG_FONT + (max(arc_heights) + 1) * _ARC_HEIGHT_UNIT
    svg_width = centers[-1] + label_widths[-1] / 2 + _BIG_FONT
    svg_height = baseline + max(label_heights) + _BIG_FONT

    # Assign UID.
    global _UID
    uid = 'svg%i' % _UID
    _UID += 1

    # Start drawing.
    file.write(u'    <svg width="%i" height="%i" class="%s">\n' %
        (svg_width, svg_height, uid))

    # Write hover styles.
    if not static:
        file.write(u'      <style type="text/css">\n')
        for node in range(1, N + 1):
            # Start with head.
            styles = _HEAD_HOVER_STYLES
            head = tree.heads(node)
            # Iterate through all parents.
            while head != 0:
                # Highlight a node its arc when head's label is hovered over.
                for style in styles:
                    file.write(u'        .%s .w%i:hover ~ %s\n' %
                        (uid, head, style % node))
                # Go to head's head.
                head = tree.heads(head)
                styles = _PARENT_HOVER_STYLES
        file.write(u'      </style>\n')

    # Write text and arcs in topsorted order.
    queue = tree.children(0)[:]
    i = 0

    while i < len(queue):
        node = queue[i]
        head = tree.heads(node)
        center = centers[node - 1]
        height = arc_heights[node - 1]
        deprel = tree.deprels(node)
        label_cls = 'w%i' % node
        if node in highlight_nodes:
            label_cls += ' user-hl'
        arc_cls = 'a%i' % node

        # Draw label.
        _draw_label(file, labels[node - 1], center, baseline, label_cls)

        # Draw arc.
        if head == 0:
            _draw_root_arc(file, center, baseline, height, deprel, arc_cls)
        else:
            head_center = centers[head - 1]
            head_center += _parent_arc_start_offset(tree, node)
            _draw_arc(file, head_center, center, baseline, height, deprel, arc_cls)

        # Enqueue children.
        queue += tree.children(node)
        i += 1

    # Done.
    file.write(u'    </svg>\n')

def write_epilogue_html(file):
    file.write(_EPILOGUE_HTML)
