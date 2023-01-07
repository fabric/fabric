#!/usr/bin/env python

import os
import setuptools

# Enable the option of building/installing Fabric 2.x as "fabric2". This allows
# users migrating from 1.x to 2.x to have both in the same process space and
# migrate piecemeal.
#
# NOTE: this requires some irritating tomfoolery; to wit:
# - the repo has a fabric2/ symlink to fabric/ so that things looking for
# fabric2/<whatever> will find it OK, whether that's code in here or deeper in
# setuptools/wheel/etc
# - wheels do _not_ execute this on install, only on generation, so maintainers
# just build wheels with the env var below turned on, and those wheels install
# 'fabric2' no problem
# - sdists execute this _both_ on package creation _and_ on install, so the env
# var only helps with inbound package metadata; on install by a user, if they
# don't have the env var, they'd end up with errors because this file tries to
# look in fabric/, not fabric2/
# - thus, we use a different test that looks locally to see if only one dir
# is present, and that overrides the env var test.
#
# See also sites/www/installing.txt.

env_wants_v2 = os.environ.get("PACKAGE_AS_FABRIC2", False)

here = os.path.abspath(os.path.dirname(__file__))
fabric2_present = os.path.isdir(os.path.join(here, "fabric2"))
fabric_present = os.path.isdir(os.path.join(here, "fabric"))
only_v2_present = fabric2_present and not fabric_present

package_name = "fabric"
binary_name = "fab"
if env_wants_v2 or only_v2_present:
    package_name = "fabric2"
    binary_name = "fab2"
packages = setuptools.find_packages(
    include=[package_name, "{}.*".format(package_name)]
)

# Version info -- read without importing
_locals = {}
with open(os.path.join(package_name, "_version.py")) as fp:
    exec(fp.read(), None, _locals)
version = _locals["__version__"]

setuptools.setup(
    name=package_name,
    version=version,
    description="High level SSH command execution",
    license="BSD",
    long_description=open("README.rst").read(),
    author="Jeff Forcier",
    author_email="jeff@bitprophet.org",
    url="https://fabfile.org",
    project_urls={
        "Docs": "https://docs.fabfile.org",
        "Source": "https://github.com/fabric/fabric",
        "Issues": "https://github.com/fabric/fabric/issues",
        "Changelog": "https://www.fabfile.org/changelog.html",
        "CI": "https://app.circleci.com/pipelines/github/fabric/fabric",
        "Twitter": "https://twitter.com/pyfabric",
    },
    python_requres=">=3.6",
    install_requires=["invoke>=2.0", "paramiko>=2.4"],
    extras_require={
        # For folks who want to use fabric.testing package, eg
        # MockRemote/MockSFTP
        "testing": [],  # no longer (for now?) needs anything special
        # For folks who want to use fabric.testing.fixtures' pytest fixtures
        "pytest": ["pytest>=7"],
    },
    packages=packages,
    entry_points={
        "console_scripts": [
            "{} = {}.main:program.run".format(binary_name, package_name)
        ]
    },
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Environment :: Console",
        "Intended Audience :: Developers",
        "Intended Audience :: System Administrators",
        "License :: OSI Approved :: BSD License",
        "Operating System :: POSIX",
        "Operating System :: Unix",
        "Operating System :: MacOS :: MacOS X",
        "Operating System :: Microsoft :: Windows",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Software Development",
        "Topic :: Software Development :: Build Tools",
        "Topic :: Software Development :: Libraries",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: System :: Clustering",
        "Topic :: System :: Software Distribution",
        "Topic :: System :: Systems Administration",
    ],
)
