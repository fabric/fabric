#!/usr/bin/env python

from __future__ import with_statement

import sys

from setuptools import setup, find_packages

from fabric.version import get_version


with open('README.rst') as f:
    readme = f.read()

long_description = """
To find out what's new in this version of Fabric, please see `the changelog
<http://docs.fabfile.org/en/%s/changelog.html>`_.

You can also install the `in-development version
<https://github.com/fabric/fabric/tarball/master#egg=fabric-dev>`_ using
pip, with `pip install fabric==dev`.

----

%s

----

For more information, please see the Fabric website or execute ``fab --help``.
""" % (get_version('branch'), readme)

if sys.version_info[:2] < (2, 6):
    install_requires=['paramiko>=1.10,<1.13']
else:
    install_requires=['paramiko>=1.10']


setup(
    name='Fabric',
    version=get_version('short'),
    description='Fabric is a simple, Pythonic tool for remote execution and deployment.',
    long_description=long_description,
    author='Jeff Forcier',
    author_email='jeff@bitprophet.org',
    url='http://fabfile.org',
    packages=find_packages(),
    test_suite='nose.collector',
    tests_require=['nose', 'fudge<1.0'],
    install_requires=install_requires,
    entry_points={
        'console_scripts': [
            'fab = fabric.main:main',
        ]
    },
    classifiers=[
          'Development Status :: 5 - Production/Stable',
          'Environment :: Console',
          'Intended Audience :: Developers',
          'Intended Audience :: System Administrators',
          'License :: OSI Approved :: BSD License',
          'Operating System :: MacOS :: MacOS X',
          'Operating System :: Unix',
          'Operating System :: POSIX',
          'Programming Language :: Python',
          'Programming Language :: Python :: 2.5',
          'Programming Language :: Python :: 2.6',
          'Programming Language :: Python :: 2.7',
          'Topic :: Software Development',
          'Topic :: Software Development :: Build Tools',
          'Topic :: Software Development :: Libraries',
          'Topic :: Software Development :: Libraries :: Python Modules',
          'Topic :: System :: Clustering',
          'Topic :: System :: Software Distribution',
          'Topic :: System :: Systems Administration',
    ],
)
