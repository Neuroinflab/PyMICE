#!/usr/bin/python
# -*- coding: utf-8 -*-
from distutils.core import setup, Extension
cPymice = Extension('pymice._C', sources = ['pymice.cpp'])
setup(name = 'pymice',
      version = '0.1',
      description = 'pymice',
      ext_modules = [cPymice],
      packages = ['pymice'])
