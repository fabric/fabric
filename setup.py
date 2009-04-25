#!/usr/bin/env python

from setuptools import setup

setup(
    name='Fabric',
    version=__import__('fabric').get_version(),
    description='Fabric is a simple, Pythonic tool for remote execution and deployment.',
    long_description=open('README').read() + """
    
For more information, please see the Fabric website or execute ``fab --help``.
""",
    author='Jeff Forcier',
    author_email='jeff@bitprophet.org',
    url='http://fabfile.org',
    install_requires=['paramiko >=1.7, <2.0'],
    py_modules=['fabric'],
    entry_points={
        'console_scripts': [
            'fab = fabric.main:main',
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
          'Topic :: Software Development',
          'Topic :: Software Development :: Build Tools',
          'Topic :: Software Development :: Libraries',
          'Topic :: Software Development :: Libraries :: Python Modules',
          'Topic :: System :: Clustering',
          'Topic :: System :: Software Distribution',
          'Topic :: System :: Systems Administration',
    ],
)
