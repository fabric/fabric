#!/usr/bin/env python

from __future__ import with_statement

import sys

from setuptools import setup, find_packages

from fabric.version import get_version


with open('README.rst') as f:
    readme = f.read()

long_description = """
Fabric3 is a fork of `Fabric <http://fabfile.org>`_ to provide compatability
with Python 3.4+. The port still works with Python 2.7. Any new releases of
Fabric will also be released here.

To find out what's new in this version of Fabric, please see `the changelog
<http://fabfile.org/changelog.html>`_.

----

%s

----

For more information, please see the Fabric website or execute ``fab --help``.
""" % (readme)

install_requires=['paramiko>=1.15.3', 'six>=1.9.0']


setup(
    name='Fabric3',
    version=get_version('short'),
    description='Fabric is a simple, Pythonic tool for remote execution and deployment (py2.7/py3.4+ compatible fork).',
    long_description=long_description,
    author='Jeff Forcier',
    author_email='jeff@bitprophet.org',
    maintainer='Mathias Ertl',
    maintainer_email='mati@er.tl',
    url='https://github.com/mathiasertl/fabric/',
    packages=find_packages(),
    test_suite='nose.collector',
    tests_require=['nose', 'fudge<1.0', 'jinja2'],
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
          'Programming Language :: Python :: 2.7',
          'Programming Language :: Python :: 3.4',
          'Topic :: Software Development',
          'Topic :: Software Development :: Build Tools',
          'Topic :: Software Development :: Libraries',
          'Topic :: Software Development :: Libraries :: Python Modules',
          'Topic :: System :: Clustering',
          'Topic :: System :: Software Distribution',
          'Topic :: System :: Systems Administration',
    ],
)
