#!/usr/bin/env python
# encoding: utf-8
###############################################################################
#                                                                             #
#    PyMICE library                                                           #
#                                                                             #
#    Copyright (C) 2017 Jakub M. Dzik a.k.a. Kowalski (Laboratory of          #
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

import unittest

from pymice._dependencies import moduleDependencies

class TestModuleDependencies(unittest.TestCase):
  class Dummy(object):
    def __init__(self, **attrs):
      for k, v in attrs.items():
        setattr(self, k, v)

  def testRaisesUnnamedModuleExceptionGivenUnnamedModule(self):
    with self.assertRaises(moduleDependencies.UnnamedModuleException):
      moduleDependencies(self.Dummy())

  def testRaisesAttributeErrorGivenUnnamedModule(self):
    with self.assertRaises(AttributeError):
      moduleDependencies(self.Dummy())

  def testOneModuleNoVersionNoDeps(self):
    self.checkApplicationResult({'name': (None, {})},
                                self.Dummy(__name__='name'))

  def testOneModuleVersionNoDeps(self):
    self.checkApplicationResult({'name': ('version', {})},
                                self.Dummy(__name__='name',
                                           __version__="version"))

  def testOneModuleVersionDeps(self):
    self.checkApplicationResult({'name': ('version', {}),
                                 'dependency': ('dependencyVersion', {})},
                                self.Dummy(__name__='name', __version__="version",
                                           __dependencies__={'dependency': ('dependencyVersion', {})}))

  def testManyModulesOfUniqueDependencies(self):
    self.checkApplicationResult({'name': ('version', {}),
                                 'name2': (None, {}),
                                 'dependency': ('dependencyVersion', {})
                      },
                     self.Dummy(__name__='name',
                                __version__="version",
                                __dependencies__={'dependency': ('dependencyVersion', {})}),
                     self.Dummy(__name__='name2'))

  def testManyModulesOfSameDependencies(self):
    self.checkApplicationResult({'name': ('version', {}),
                                 'name2': (None, {}),
                                 'dependency': ('dependencyVersion', {})
                      },
                     self.Dummy(__name__='name',
                                __version__="version",
                                __dependencies__={'dependency': ('dependencyVersion', {})}),
                     self.Dummy(__name__='name2',
                                __dependencies__={'dependency': ('dependencyVersion', {})}))

  def testManyModulesOfConflictingDependencies(self):
    self.checkApplicationResult({'name': ('version', {'dependency': ('A', {})}),
                                 'name2': (None, {'dependency': ('B', {})}),
                                 'dependency2': ('C', {'d': (None, {})}),
                                 },
                                self.Dummy(__name__='name',
                                           __version__="version",
                                           __dependencies__={'dependency': ('A', {}),
                                                             'dependency2': ('C', {'d': (None, {})})}),
                                self.Dummy(__name__='name2',
                                           __dependencies__={'dependency': ('B', {}),
                                                             'dependency2': ('C', {'d': (None, {})})}))

  def checkApplicationResult(self, expected, *modules):
    self.assertEqual(expected,
                     moduleDependencies(*modules))


if __name__ == '__main__':
    unittest.main()