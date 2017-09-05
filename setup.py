#!/usr/bin/env python
# encoding: utf-8
###############################################################################
#                                                                             #
#    PyMICE library                                                           #
#                                                                             #
#    Copyright (C) 2014-2017 Jakub M. Dzik aka Kowalski (Laboratory of        #
#    Neuroinformatics; Nencki Institute of Experimental Biology of Polish     #
#    Academy of Sciences)                                                     #
#                                                                             #
#    This software is free software: you can redistribute it and/or modify    #
#    it under the terms of the GNU General Public License as published by     #
#    the Free Software Foundation, either version 3 of the License, or        #
#    (at your option) any later version.                                      #
#                                                                             #
#    This software is distributed in the hope that it will be useful,         #
#    but WITHOUT ANY WARRANTY; without even the implied warranty of           #
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the            #
#    GNU General Public License for more details.                             #
#                                                                             #
#    You should have received a copy of the GNU General Public License        #
#    along with this software.  If not, see http://www.gnu.org/licenses/.     #
#                                                                             #
###############################################################################

import os, sys
from lib.pymice import __version__

try:
  from setuptools import setup, Extension
  # XXX a fix for https://bugs.python.org/issue23246 bug

except ImportError:
  from distutils.core import setup, Extension
  print("The setuptools module is not found - 'Unable to find vcvarsall.bat' error")
  print("(and many others) might occur.")
  print("")
  setuptoolsPresent = False

else:
  setuptoolsPresent = True


def loadUTF8(path):
  if sys.version_info.major >= 3:
    return open(path, encoding='utf-8').read()

  return open(path).read().decode('utf-8')

def loadTextFrom(path):
  return loadUTF8(os.path.join(os.path.dirname(__file__),
                               path))

cPymice = Extension('pymice._C', sources = ['pymice.cpp'])
setup(name = 'PyMICE',
      version = __version__,
      url = 'https://neuroinflab.wordpress.com/research/pymice/',
      description = 'PyMICE - a Python® library for mice behavioural data analysis',
      long_description = loadTextFrom('README.rst'),
      author="Jakub M. Dzik a.k.a. Kowalski, S. Leski (Laboratory of Neuroinformatics; Nencki Institute of Experimental Biology)",
      author_email="jakub.m.dzik+pymice@gmail.com, sz.leski+pymice@gmail.com",
      license='GPL3',
      classifiers = ['Development Status :: 5 - Production/Stable',
                     'Intended Audience :: Developers',
                     'Intended Audience :: Science/Research',
                     'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
                     'Natural Language :: English',
                     'Operating System :: OS Independent',
                     'Programming Language :: C',
                     'Programming Language :: Python',
                     'Programming Language :: Python :: 2',
                     'Programming Language :: Python :: 2.7',
                     'Programming Language :: Python :: 3',
                     'Programming Language :: Python :: 3.3',
                     'Programming Language :: Python :: 3.4',
                     'Programming Language :: Python :: 3.5',
                     'Programming Language :: Python :: 3.6',
                     'Topic :: Scientific/Engineering',
                     'Topic :: Scientific/Engineering :: Bio-Informatics',
                     'Topic :: Software Development',
                     'Topic :: Software Development :: Libraries :: Python Modules'],
      keywords ='IntelliCage mice behavioural data loading analysis',
      ext_modules = [cPymice],
      packages = ['pymice',
                  'pymice._Python{.major}'.format(sys.version_info),
                  ],
      package_dir = {'': 'lib'},
      package_data={'pymice': ['data/tutorial/demo.zip',
                               'data/tutorial/LICENSE',
                               'data/tutorial/COPYING',
                               'data/tutorial/C57_AB/*.zip',
                               'data/tutorial/C57_AB/timeline.ini',
                               'data/tutorial/C57_AB/LICENSE',
                               'data/tutorial/C57_AB/COPYING',
                               'data/tutorial/FVB/*.zip',
                               'data/tutorial/FVB/timeline.ini',
                               'data/tutorial/FVB/LICENSE',
                               'data/tutorial/FVB/COPYING',
                               ]},
      requires=['dateutil',
                'matplotlib',
                'numpy',
                'pytz'])
