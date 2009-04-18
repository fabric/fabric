#!/usr/bin/env python

from setuptools import setup

setup(
    name = 'Fabric',
    version = __import__('fabric').get_version()
    description = 'Fabric is a simple, Pythonic tool for remote execution and deployment.',
    long_description = """
Fabric is designed to streamline the process of interacting with remote
servers, typically via SSH, for the purposes of deploying applications or
performing system administration tasks. It provides tools for running arbitrary
shell commands (either as a normal login user, or via ``sudo``), uploading and downloading files, and so forth. 

Typical use involves defining a "fabfile", a Python module defining one or more
functiona/tasks, which may then be executed (one or more at a time) by the
``fab`` command-line tool. Fabric provides extra functionality related to this
mode of use, such as prompting for user input, ensuring certain variables are
present in order for tasks to run, and specifying which host or hosts a
specific task connects to by default.

Fabric may also be used as a standalone library, so that other Python programs
needing a simple API on top of SSH or SCP may import and utilize specific
pieces of Fabric functionality.

For more information, please see the project website, or ``fab --help``.
""",
    author = 'Jeff Forcier',
    author_email = 'jeff@bitprophet.org',
    url = 'http://fabfile.org',
    install_requires = ['paramiko >=1.7, <2.0'],
    py_modules = ['fabric'],
    entry_points = {
        'console_scripts': [
            'fab = fabric.main:main',
        ]
    },
    classifiers = [
          'Development Status :: 3 - Alpha',
          'Environment :: Console',
          'Intended Audience :: Developers',
          'Intended Audience :: System Administrators',
          'License :: OSI Approved :: BSD License',
          'Operating System :: MacOS :: MacOS X',
          'Operating System :: Unix',
          'Operating System :: POSIX',
          'Programming Language :: Python',
          'Topic :: Software Development',
          'Topic :: Software Development :: Build Tools',
          'Topic :: Software Development :: Libraries',
          'Topic :: Software Development :: Libraries :: Python Modules',
          'Topic :: System :: Clustering',
          'Topic :: System :: Software Distribution',
          'Topic :: System :: Systems Administration',
    ],
)
