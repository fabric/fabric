#!/usr/bin/env python

# Support setuptools or distutils
try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

# Version info -- read without importing
_locals = {}
with open('fabric/_version.py') as fp:
    exec(fp.read(), None, _locals)
version = _locals['__version__']

# Frankenstein long_description: changelog note + README
long_description = """
To find out what's new in this version of Fabric, please see `the changelog
<http://fabfile.org/changelog.html>`_.

{0}
""".format(open('README.rst').read())

setup(
    name='fabric',
    version=version,
    description='High level SSH command execution',
    license='BSD',

    long_description=long_description,
    author='Jeff Forcier',
    author_email='jeff@bitprophet.org',
    url='http://fabfile.org',

    install_requires=[
        # TODO: pinning
        'invoke',
        'paramiko',
    ],
    packages=['fabric'],
    #entry_points={
    #    'console_scripts': [
    #        'fabric = fabric.cli:main',
    #        'fab = fabric.cli:main',
    #    ]
    #},

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
          'Programming Language :: Python :: 2.6',
          'Programming Language :: Python :: 2.7',
          'Programming Language :: Python :: 3.2',
          'Programming Language :: Python :: 3.3',
          'Topic :: Software Development',
          'Topic :: Software Development :: Build Tools',
          'Topic :: Software Development :: Libraries',
          'Topic :: Software Development :: Libraries :: Python Modules',
          'Topic :: System :: Clustering',
          'Topic :: System :: Software Distribution',
          'Topic :: System :: Systems Administration',
    ],
)
