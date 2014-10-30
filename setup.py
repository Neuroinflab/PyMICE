#!/usr/bin/python
# -*- coding: utf-8 -*-
from distutils.core import setup, Extension
module1 = Extension('PyMICE_C', sources = ['PyMICE.cpp'])
setup(name = 'PyMICE_C',
      version = '0.1',
      description = 'C++ booster for PyMICE',
      ext_modules = [module1])
