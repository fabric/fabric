# Obtain shared config values
import os, sys
from os.path import abspath, join, dirname

sys.path.append(abspath(join(dirname(__file__), "..")))
sys.path.append(abspath(join(dirname(__file__), "..", "..")))
from shared_conf import *

# Enable & configure autodoc
extensions.append("sphinx.ext.autodoc")
autodoc_default_flags = ["members", "special-members"]

# Enable & configure doctest
extensions.append("sphinx.ext.doctest")
# Import mock tooling from unit tests' _util.py
doctest_path = [abspath(join(dirname(__file__), "..", "..", "tests"))]
doctest_global_setup = r"""
from _util import MockRemote, MockSFTP, Session, Command
"""

# Default is 'local' building, but reference the public WWW site when building
# under RTD.
target = join(dirname(__file__), "..", "www", "_build")
if on_rtd:
    target = "http://www.fabfile.org/"
www = (target, None)
# Intersphinx connection to www site
intersphinx_mapping.update({"www": www})

# Sister-site links to WWW
html_theme_options["extra_nav_links"] = {
    "Main website": "http://www.fabfile.org"
}
