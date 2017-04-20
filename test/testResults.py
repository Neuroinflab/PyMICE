#!/usr/bin/env python
# encoding: utf-8
###############################################################################
#                                                                             #
#    PyMICE library                                                           #
#                                                                             #
#    Copyright (C) 2015-2017 Jakub M. Dzik a.k.a. Kowalski, S. Łęski          #
#    (Laboratory of Neuroinformatics; Nencki Institute of Experimental        #
#    Biology of Polish Academy of Sciences)                                   #
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

from unittest import TestCase

from pymice._Results import lazyAttribute

class TestLazyAttribute(TestCase):
  class TestObject(object):
    def __init__(self, valueGenerator):
      self.getAttributeValue = valueGenerator

    @lazyAttribute
    def dynamicAttribute(self):
      return self.getAttributeValue()

  def functionGeneratingTheValue(self):
    self.functionCall += 1
    return 1337

  def setUp(self):
    self.obj = self.TestObject(self.functionGeneratingTheValue)
    self.functionCall = 0

  def testAttributeValue(self):
    self.assertEqual(1337, self.obj.dynamicAttribute)

  def testAttributeLaziness(self):
    self.assertEqual(0, self.functionCall)
    self.obj.dynamicAttribute
    self.assertEqual(1, self.functionCall)

  def testAttributeCaching(self):
    self.assertEqual(0, self.functionCall)
    self.obj.dynamicAttribute
    self.assertEqual(1, self.functionCall)
    self.assertEqual(1337, self.obj.dynamicAttribute)
    self.assertEqual(1, self.functionCall)
