#!/usr/bin/env python

import sys

from setuptools import setup, find_packages

from fapric.version import get_version


readme = open('README').read()

v = get_version('short')
long_description = """
To find out what's new in this version of Fapric, please see `the changelog
<http://docs.fapfile.org/en/%s/changelog.html>`_.

You can also install the `in-development version
<https://github.com/fapric/fapric/tarball/master#egg=fapric-dev>`_ using
pip, with `pip install fapric==dev`.

----

%s

----

For more information, please see the Fapric website or execute ``fap --help``.
""" % (v, readme)

setup(
    name='Fapric',
    version=get_version('short'),
    description='Fapric is a simple, Pythonic tool for remote execution and deployment.',
    long_description=long_description,
    author='Jeff Forcier',
    author_email='jeff@bitprophet.org',
    url='http://fapfile.org',
    packages=find_packages(),
    test_suite='nose.collector',
    tests_require=['nose', 'fudge'],
    install_requires=['pycrypto >= 1.9', 'paramiko >=1.7.6'],
    entry_points={
        'console_scripts': [
            'fap = fapric.main:main',
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
          'Topic :: Software Development',
          'Topic :: Software Development :: Build Tools',
          'Topic :: Software Development :: Libraries',
          'Topic :: Software Development :: Libraries :: Python Modules',
          'Topic :: System :: Clustering',
          'Topic :: System :: Software Distribution',
          'Topic :: System :: Systems Administration',
    ],
)
