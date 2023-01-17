import os
from os.path import join, dirname, abspath
from datetime import datetime

from invocations.environment import in_ci
import alabaster


# Alabaster theme + mini-extension
html_theme_path = [alabaster.get_path()]
extensions = ["alabaster", "sphinx.ext.intersphinx"]

# Paths relative to invoking conf.py - not this shared file
html_static_path = [join("..", "_shared_static")]
html_theme = "alabaster"
html_theme_options = {
    "logo": "logo.png",
    "logo_name": True,
    "logo_text_align": "center",
    "description": "Pythonic remote execution",
    "github_user": "fabric",
    "github_repo": "fabric",
    "travis_button": False,  # Circle now
    "codecov_button": False,  # README badge now
    "tidelift_url": "https://tidelift.com/subscription/pkg/pypi-fabric?utm_source=pypi-fabric&utm_medium=referral&utm_campaign=docs",
    "analytics_id": "UA-18486793-1",
    "link": "#3782BE",
    "link_hover": "#3782BE",
    # Wide enough that 80-col code snippets aren't truncated on default font
    # settings (at least for bitprophet's Chrome-on-OSX-Yosemite setup)
    "page_width": "1024px",
}
html_sidebars = {
    "**": ["about.html", "navigation.html", "searchbox.html", "donate.html"]
}

# Enable & configure doctest
extensions.append("sphinx.ext.doctest")
doctest_global_setup = r"""
from fabric.testing.base import MockRemote, MockSFTP, Session, Command
"""

on_rtd = os.environ.get("READTHEDOCS") == "True"
on_dev = not (on_rtd or in_ci())

# Invoke (docs + www)
inv_target = join(
    dirname(__file__), "..", "..", "invoke", "sites", "docs", "_build"
)
if not on_dev:
    inv_target = "https://docs.pyinvoke.org/en/latest/"
inv_www_target = join(
    dirname(__file__), "..", "..", "invoke", "sites", "www", "_build"
)
if not on_dev:
    inv_www_target = "https://pyinvoke.org/"
# Paramiko (docs)
para_target = join(
    dirname(__file__), "..", "..", "paramiko", "sites", "docs", "_build"
)
if not on_dev:
    para_target = "https://docs.paramiko.org/en/latest/"
intersphinx_mapping = {
    "python": ("https://docs.python.org/", None),
    "invoke": (inv_target, None),
    "invoke_www": (inv_www_target, None),
    "paramiko": (para_target, None),
}

# Regular settings
project = "Fabric"
copyright = f"{datetime.now().year} Jeff Forcier"
master_doc = "index"
templates_path = ["_templates"]
exclude_trees = ["_build"]
source_suffix = ".rst"
default_role = "obj"
