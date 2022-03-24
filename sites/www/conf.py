# Obtain shared config values
import sys
import os
from os.path import abspath, join, dirname

sys.path.append(abspath(join(dirname(__file__), "..")))
from shared_conf import *


# Releases changelog extension
extensions.append("releases")
releases_document_name = ["changelog", "changelog-v1"]
releases_github_path = "fabric/fabric"

# Intersphinx for referencing API/usage docs
extensions.append("sphinx.ext.intersphinx")
# Default is 'local' building, but reference the public docs site when building
# under RTD.
target = join(dirname(__file__), "..", "docs", "_build")
if on_rtd:
    target = "https://docs.fabfile.org/en/latest/"
intersphinx_mapping.update({"docs": (target, None)})

# Sister-site links to API docs
html_theme_options["extra_nav_links"] = {
    "API Docs": "https://docs.fabfile.org"
}
