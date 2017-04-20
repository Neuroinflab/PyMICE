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

import collections
import datetime
import operator
import unittest

from pymice._Tools import groupBy, convertTime

Pair = collections.namedtuple('Pair', ['a', 'b'])

class TestGroupBy(unittest.TestCase):
  def testGivenKeyFunctionAsKeywordAttributeGroupsByItsResult(self):
    self.assertEqual({1: [(1, 1), (2, 1, 8)],
                      2: [(1, 2), (3, 2)],
                      4: [(3, 4)]},
                     groupBy([(1, 2), (3, 4), (3, 2), (1, 1), (2, 1, 8)],
                             getKey=operator.itemgetter(1)))

  def testGivenKeyFunctionAsPositionalAttributeGroupsByItsResult(self):
    self.assertEqual({2: [(0, 2), (1, 1), (1, 1)],
                      3: [(1, 2), (2, 1), (3, 0)]},
                     groupBy([(1, 2), (2, 1), (0, 2), (3, 0), (1, 1), (1, 1)],
                             lambda x: x[0] + x[1]))

  def testGivenTypeAsKeyFunctionGroupsByItsResult(self):
    self.assertEqual({'2': [2, 2],
                      '3': [3]},
                     groupBy([2, 3, 2],
                             getKey=str))

  def testGivenNoObjectsReturnsEmptyDict(self):
    self.assertEqual({},
                     groupBy([], getKey=lambda x: x[0] + x[1]))

  def testGivenNameOfAttributeGroupsByTheAttribute(self):
    self.assertEqual({1: [(1, 2), (1, 1)],
                      2: [(2, 1)]},
                     groupBy([Pair(1, 2), Pair(1, 1), Pair(2, 1)], 'a'))

  def testGivenTupleOfNamesOfAttributesGroupsByTheirCombination(self):
    self.assertEqual({(1, 1): [(1, 1)],
                      (1, 2): [(1, 2)],
                      (2, 1): [(2, 1)]},
                     groupBy([Pair(1, 2), Pair(1, 1), Pair(2, 1)], ('a', 'b')))

  def testKeyFunctionDefaultsToIdentity(self):
    self.assertEqual({1: [1],
                      2: [2]},
                     groupBy([1, 2]))

  def testOutputAlwaysContainsRequiredKeys(self):
    self.assertEqual({1: [1],
                      'a': []},
                     groupBy([1], requiredKeys=['a']))

  def testRequiredKeysDoNotConflictWithKeysDefinedByInput(self):
    self.assertEqual({1: [1]},
                     groupBy([1], requiredKeys=[1]))


class TestConvertTime(unittest.TestCase):
  def testConvertsGivenTimestringReturnsNaiveDatetime(self):
    time = convertTime('1970-01-01 12:34:56.7')
    self.assertIsInstance(time, datetime.datetime)
    for (attr, value) in [('year', 1970),
                          ('month', 1),
                          ('day', 1),
                          ('hour', 12),
                          ('minute', 34),
                          ('second', 56),
                          ('microsecond', 700000),
                          ('tzinfo', None)]:
      self.assertEqual(value, getattr(time, attr))


if __name__ == '__main__':
  unittest.main()
