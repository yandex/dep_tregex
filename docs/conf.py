#!/usr/bin/env python3

import sys
import os
import time

## ----------------------------------------------------------------------------
#                             Sphinx configuration

# Enabled Sphinx extensions
extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.intersphinx',
    'sphinx.ext.extlinks',
    'sphinx.ext.mathjax',
]

# Default reStructuredText role.
default_role = None

# Print warnings for every missing reference
nitpicky = True

# Class or enumeration members are usually written in the same order it would
# be good to document them
autodoc_member_order = "bysource"

# Master document is index.rst
master_doc = "index"

## ----------------------------------------------------------------------------
#                             Options for HTML output

html_theme_options = {"nosidebar": True}
html_use_smartypants = True
html_show_sourcelink = True

# Customize footer
#
html_last_updated_fmt = "%b %d, %Y"
html_use_index = True
html_use_modindex = True
html_show_sphinx = True
html_show_copyright = True

## ----------------------------------------------------------------------------
#                             Intersphinx configuration

intersphinx_mapping = {}

# Set up intersphinx for official Python 2 documentation
intersphinx_mapping['python'] = ("http://docs.python.org/2", None)

## ----------------------------------------------------------------------------
#                           Project-specific configuration

project = "dep_tregex"
copyright = "Yandex"
