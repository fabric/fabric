#!/usr/bin/env python

import os
import setuptools

# Enable the option of building/installing Fabric 2.x as "fabric2". This allows
# users migrating from 1.x to 2.x to have both in the same process space and
# migrate piecemeal. It leverages the fact that the Git repository holds a
# symbolic link from 'fabric' to 'fabric2' (so it effectively has a 'copy' of
# the code under either name).
#
# NOTE: this only works when one is executing setup.py directly (e.g. it cannot
# be triggered when installing a wheel or other binary archive); the
# maintainers take care of triggering this explicitly at build time so that two
# different wheels & PyPI entries are in play.
#
# See also sites/www/installing.txt.
package_name = 'fabric'
binary_name = 'fab'
if os.environ.get('PACKAGE_AS_FABRIC2', None):
    package_name = 'fabric2'
    binary_name = 'fab2'

# Version info -- read without importing
_locals = {}
with open(os.path.join(package_name, '_version.py')) as fp:
    exec(fp.read(), None, _locals)
version = _locals['__version__']

# Frankenstein long_description: changelog note + README
long_description = """
To find out what's new in this version of Fabric, please see `the changelog
<http://fabfile.org/changelog.html>`_.

{0}
""".format(open('README.rst').read())

setuptools.setup(
    name=package_name,
    version=version,
    description='High level SSH command execution',
    license='BSD',

    long_description=long_description,
    author='Jeff Forcier',
    author_email='jeff@bitprophet.org',
    url='http://fabfile.org',

    install_requires=[
        'invoke>=0.15,<2.0',
        'paramiko>=2.1,<3.0',
        'cryptography>=1.1,<2.0',
    ],
    packages=[package_name],
    entry_points={
        'console_scripts': [
            '{0} = {1}.main:program.run'.format(binary_name, package_name),
        ]
    },

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
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Topic :: Software Development',
        'Topic :: Software Development :: Build Tools',
        'Topic :: Software Development :: Libraries',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Topic :: System :: Clustering',
        'Topic :: System :: Software Distribution',
        'Topic :: System :: Systems Administration',
    ],
)
