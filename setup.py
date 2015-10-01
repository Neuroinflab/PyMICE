#!/usr/bin/python
# -*- coding: utf-8 -*-
###############################################################################
#                                                                             #
#    PyMICE library                                                           #
#                                                                             #
#    Copyright (C) 2014-2015 Jakub M. Kowalski (Laboratory of                 #
#    Neuroinformatics; Nencki Institute of Experimental Biology)              #
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



cPymice = Extension('pymice._C', sources = ['pymice.cpp'])
#install_requires = ['numpy']?
setup(name = 'PyMICE',
      version = '0.2.1',
      url = 'https://neuroinflab.wordpress.com/research/pymice/',
      description = 'PyMICE - a Python™ library for mice behavioural data analysis',
      long_description="""PyMICE is a Python™ library for mice behavioural data analysis.

The library can be used for loading and analysing of data obtained from IntelliCage™ system in an intuitive way in Python programming language.

The library provides user with an object oriented application programming interface (API) and a data abstraction layer. It also comes with auxiliary tools supporting development of analysis workflows, like data validators and a tool for workflow configuration.""",
      author="Jakub M. Kowalski, S. Leski (Laboratory of Neuroinformatics; Nencki Institute of Experimental Biology)",
      author_email="j.kowalski@nencki.gov.pl, s.leski@nencki.gov.pl",
      license='GPL3',
      classifiers = ['Development Status :: 4 - Beta',
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
                     'Topic :: Scientific/Engineering',
                     'Topic :: Scientific/Engineering :: Bio-Informatics',
                     'Topic :: Software Development',
                     'Topic :: Software Development :: Libraries :: Python Modules'],
      keywords ='IntelliCage mice behavioural data loading analysis',
      ext_modules = [cPymice],
      packages = ['pymice'])
