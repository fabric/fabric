#!/usr/bin/env python

from setuptools import setup

setup(
    name = 'Fabric',
    version = '0.0.9',
    description = 'Fabric is a simple pythonic remote deployment tool.',
    long_description = """
It is designed to upload files to, and run shell commands on, a number of
servers in parallel or serially. These commands are grouped in tasks (regular
python functions) and specified in a 'fabfile.'

This is called remote automation, and the primary use case is deploying
applications to multiple similar hosts.

Although it is easier to automate when the target hosts are similar, it is not
a requirement and Fabric has features for working with heterogeneous hosts as
well.

Once installed, you can run `fab help` to learn more about how to use Fabric.
""",
    author = 'Christian Vest Hansen',
    author_email = 'karmazilla@gmail.com',
    url = 'http://www.nongnu.org/fab/',
    install_requires = ['paramiko >=1.6, <2.0'],
    py_modules = ['fabric'],
    entry_points = {
        'console_scripts': [
            'fab = fabric:main',
        ]
    },
    classifiers = [
          'Development Status :: 3 - Alpha',
          'Environment :: Console',
          'Intended Audience :: Developers',
          'Intended Audience :: System Administrators',
          'License :: OSI Approved :: GNU General Public License (GPL)',
          'Operating System :: MacOS :: MacOS X',
          'Operating System :: Unix',
          'Operating System :: POSIX',
          'Programming Language :: Python',
          'Topic :: Software Development',
          'Topic :: System :: Clustering',
          'Topic :: System :: Software Distribution',
    ],
)
