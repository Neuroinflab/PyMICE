#!/usr/bin/env python
# encoding: utf-8
###############################################################################
#                                                                             #
#    PyMICE library                                                           #
#                                                                             #
#    Copyright (C) 2015-2016 Jakub M. Kowalski, S. Łęski (Laboratory of       #
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

import collections
import datetime
import operator
import unittest
import tempfile
import os
import shutil
import sys
import io

from pymice._Tools import groupBy, convertTime, getTutorialData

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
                             getKey=lambda x: x[0] + x[1]))

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


class TestGetTutorialDataBase(unittest.TestCase):
  class MockOutput(unittest.TestCase):
    _type_equality_funcs = {} # hack for unittest in Python3

    def __init__(self, expectedStdout, expectedStderr):
      self.__expectedStdout = expectedStdout
      self.__expectedStderr = expectedStderr
      self.__stdout = io.StringIO()
      self.__stderr = io.StringIO()

    def __enter__(self):
      self.__backupSysOutput()
      self.__grabSysOutput()

    def __grabSysOutput(self):
      sys.stdout = self.__stdout
      sys.stderr = self.__stderr

    def __backupSysOutput(self):
      self.__oldStdout = sys.stdout
      self.__oldStderr = sys.stderr

    def __exit__(self, exc_type, exc_val, exc_tb):
      self.__restoreSysOutput()
      if exc_type is not None:
        return False

      self.__checkIfOutputWasAsExpected()

    def __checkIfOutputWasAsExpected(self):
      self.assertEqual(self.__expectedStdout, self.__stdout.getvalue())
      self.assertEqual(self.__expectedStderr, self.__stderr.getvalue())

    def __restoreSysOutput(self):
      sys.stderr = self.__oldStderr
      sys.stdout = self.__oldStdout

  def setUp(self):
    self.__dirname = tempfile.mkdtemp(prefix='.tmp_ToolsDoctests')
    self.__cwd = os.getcwd()
    os.chdir(self.__dirname)

  def tearDown(self):
    os.chdir(self.__cwd)
    shutil.rmtree(self.__dirname)

  def checkExist(self, *paths):
    for path in paths:
      self.checkExists(path)

  def checkExists(self, path):
    self.assertTrue(os.path.exists(path))


class GivenNoDatasetPresent(TestGetTutorialDataBase):
  def testWhenDatasetFetchedItIsSavedInTheCurrentDirectory(self):
    getTutorialData(fetch='C57_AB')
    self.checkExist('C57_AB/2012-08-28 13.44.51.zip',
                    'C57_AB/2012-08-28 15.33.58.zip',
                    'C57_AB/2012-08-31 11.46.31.zip',
                    'C57_AB/2012-08-31 11.58.22.zip',
                    'C57_AB/timeline.ini',
                    'C57_AB/COPYING',
                    'C57_AB/LICENSE')

  def testWhenDatasetFetchedNoNotificationIsDisplayed(self):
    with self.MockOutput('', ''):
      getTutorialData(fetch='C57_AB')

  def testWhenUnknownDatasetRequestedNotificationIsDisplayed(self):
    with self.MockOutput('',
                         'Warning: unknown download requested (unknownDataset)\nAll datasets already present.\n'):
      getTutorialData(fetch='unknownDataset')


class GivenC57_ABDatasetPresent(TestGetTutorialDataBase):
  def setUp(self):
    super(GivenC57_ABDatasetPresent, self).setUp()
    getTutorialData(fetch='C57_AB')

  def testWhenTheDatasetFetchedNotificationIsDisplayed(self):
    with self.MockOutput('',
                         'C57_AB dataset already present\nAll datasets already present.\n'):
      getTutorialData(fetch='C57_AB')

  def testWhenTheDatasetFetchedWithQuietFlagNoNotificationDisplayed(self):
    with self.MockOutput('', ''):
      getTutorialData(fetch='C57_AB', quiet=True)

  def testWhenAllDatasetsFetchedMissingDatasetIsSavedInTheCurrentDirectory(self):
    getTutorialData()
    self.checkExist('demo.zip', 'COPYING', 'LICENSE')

  def testWhenAllDatasetsFetchedNotificationIsDisplayed(self):
    with self.MockOutput('',
                         'C57_AB dataset already present\n'):
      getTutorialData()


class GivenAllDatasetsPresent(TestGetTutorialDataBase):
  def setUp(self):
    super(GivenAllDatasetsPresent, self).setUp()
    getTutorialData()

  def testWhenAllDatasetsFetchedNotificationIsDisplayed(self):
    with self.MockOutput('',
                         'C57_AB dataset already present\ndemo dataset already present\nAll datasets already present.\n'):
      getTutorialData()


if __name__ == '__main__':
  unittest.main()
