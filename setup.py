#!/usr/bin/python
# -*- coding: utf-8 -*-
from distutils.core import setup, Extension
module1 = Extension('NeuroinfMice', sources = ['NeuroinfMice.cpp'])
setup(name = 'NeuroinfMice',
      version = '0.1',
      description = 'C++ boosted mice RL models',
      ext_modules = [module1])
