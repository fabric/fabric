#!/usr/bin/env python

from distutils.core import setup
import imp

fab = imp.load_source('fab', 'fab')

setup(
    name='Fabric',
    version=fab.__version__,
    description='Fabric is a simple pythonic remote deployment tool.',
    author=fab.__author__,
    author_email=fab.__author_email__,
    url=fab.__url__,
    requires=['paramiko (>=1.6, <2.0)'],
)