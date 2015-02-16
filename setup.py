#!/usr/bin/python
# -*- coding: utf-8 -*-
from distutils.core import setup, Extension
cPyMICE = Extension('PyMICE._C', sources = ['PyMICE.cpp'])
setup(name = 'PyMICE',
      version = '0.1',
      description = 'PyMICE',
      ext_modules = [cPyMICE],
      packages = ['PyMICE'])
