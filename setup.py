#!/usr/bin/env python

from distutils.core import setup
import fabric

setup(
    name='Fabric',
    version=fabric.__version__,
    description='Fabric is a simple pythonic remote deployment tool.',
    author=fabric.__author__,
    author_email=fabric.__author_email__,
    url=fabric.__url__,
    requires=['paramiko (>=1.6, <2.0)'],
    py_modules=['fabric'],
    scripts=['fab']
)