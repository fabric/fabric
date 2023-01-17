# Obtain shared config values
import sys
from os.path import abspath, join, dirname

sys.path.append(abspath(join(dirname(__file__), "..")))
sys.path.append(abspath(join(dirname(__file__), "..", "..")))
from shared_conf import *

# Enable & configure autodoc
extensions.append("sphinx.ext.autodoc")
# Autodoc settings
autodoc_default_options = {
    "members": True,
    "special-members": True,
}
# TODO: consider documenting things like Remote.run usefully and
# re-enabling this? new as of sphinx 1.7 and NOT the old behavior, so very
# surprising in a bunch of spots right now, where it pulls in Invoke
# docstrings that then have bad refs and so on.
autodoc_inherit_docstrings = False

# Default is 'local' building, but reference the public WWW site when building
# under RTD.
target = join(dirname(__file__), "..", "www", "_build")
if on_rtd:
    target = "https://www.fabfile.org/"
www = (target, None)
# Intersphinx connection to www site
intersphinx_mapping.update({"www": www})

# Sister-site links to WWW
html_theme_options["extra_nav_links"] = {
    "Main website": "https://www.fabfile.org"
}
