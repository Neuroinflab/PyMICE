#!/usr/bin/env python
# encoding: utf-8
###############################################################################
#                                                                             #
#    PyMICE library                                                           #
#                                                                             #
#    Copyright (C) 2015 Jakub M. Kowalski, S. Łęski (Laboratory of            #
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

import doctest
import collections
import pymice as pm
import unittest
import operator
from pymice._Tools import groupBy

Pair = collections.namedtuple('Pair', ['a', 'b'])

class TestGroupBy(unittest.TestCase):
  def testKeyFunctionItemgetter(self):
    self.assertEqual({1: [(1, 1), (2, 1, 8)],
                      2: [(1, 2), (3, 2)],
                      4: [(3, 4)]},
                     groupBy([(1, 2), (3, 4), (3, 2), (1, 1), (2, 1, 8)],
                             getKey=operator.itemgetter(1)))

  def testKeyFunctionLambda(self):
    self.assertEqual({2: [(0, 2), (1, 1), (1, 1)],
                      3: [(1, 2), (2, 1), (3, 0)]},
                     groupBy([(1, 2), (2, 1), (0, 2), (3, 0), (1, 1), (1, 1)],
                             getKey=lambda x: x[0] + x[1]))

  def testEmptyKeyFunctionLambda(self):
    self.assertEqual({},
                     groupBy([], getKey=lambda x: x[0] + x[1]))

  def testAttibute(self):
    self.assertEqual({1: [(1, 2), (1, 1)],
                      2: [(2, 1)]},
                     groupBy([Pair(1, 2), Pair(1, 1), Pair(2, 1)], 'a'))

  def testAttributeTuple(self):
    self.assertEqual({(1, 1): [(1, 1)],
                      (1, 2): [(1, 2)],
                      (2, 1): [(2, 1)]},
                     groupBy([Pair(1, 2), Pair(1, 1), Pair(2, 1)], ('a', 'b')))


def getGlobs():
  return {'Pair': Pair}

def load_tests(loader, tests, ignore):
  tests.addTests(doctest.DocTestSuite(pm._Tools, extraglobs=getGlobs()))
  return tests

if __name__ == '__main__':
  doctest.testmod(pm._Tools, extraglobs=getGlobs())
  unittest.main()
