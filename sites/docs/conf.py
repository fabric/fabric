# Obtain shared config values
import os, sys
sys.path.append(os.path.abspath('..'))
sys.path.append(os.path.abspath('../..'))
from shared_conf import *

# Enable autodoc, intersphinx
extensions.extend(['sphinx.ext.autodoc', 'sphinx.ext.intersphinx'])

# Autodoc settings
autodoc_default_flags = ['members', 'special-members']

# Intersphinx connection to stdlib
intersphinx_mapping = {
    'python': ('http://docs.python.org/2.6', None),
}

# Sister-site links to WWW
html_theme_options['extra_nav_links'] = {
    "Main website": 'http://www.fabfile.org',
}
