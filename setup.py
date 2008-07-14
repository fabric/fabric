#!/usr/bin/env python

from setuptools import setup

setup(
    name = 'Fabric',
    version = '0.0.8',
    description = 'Fabric is a simple pythonic remote deployment tool.',
    long_description = """
It is designed to upload files to, and run shell commands on, a number of
servers in parallel or serially. These commands are grouped in tasks (regular
python functions) and specified in a 'fabfile'. 

It is a bit like a dumbed down Capistrano, except it's in Python, dosn't expect
you to be deploying Rails applications, and the 'put' command works. 

Unlike Capistrano, Fabric want's to stay small, light, easy to change and not
bound to any specific framework.
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
