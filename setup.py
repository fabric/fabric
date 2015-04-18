#!/usr/bin/env python

from __future__ import with_statement
from setuptools import setup, find_packages

with open('README.rst') as f:
    README = f.read()

setup(
    name='fabric_swatch',
    version='0.1.0',
    description='Fabric-Swatch is a fork of swatch with the remote functionality and dependencies stripped out and added support for python3',
    long_description=README,
    author='Ryan Luckie',
    author_email='rtluckie@gmail.com',
    url='http://github.com/rtluckie/fabric-swatch',
    packages=find_packages('.', exclude=('tests*', 'integration*')),
    test_suite='nose.collector',
    tests_require=['nose', 'fudge<1.0', 'jinja2'],
    install_requires=['six'],
    classifiers=[
        'Development Status :: 3 - Alpha',
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
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.1',
        'Programming Language :: Python :: 3.2',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: Implementation :: CPython',
        'Programming Language :: Python :: Implementation :: PyPy',
        'Topic :: Utilities',
        'Topic :: Software Development',
        'Topic :: Software Development :: Build Tools',
        'Topic :: Software Development :: Libraries',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Topic :: System :: Software Distribution',
        'Topic :: System :: Systems Administration',
    ],
)
