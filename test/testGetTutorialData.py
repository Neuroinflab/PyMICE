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

import io
import os
import shutil
import sys
import tempfile
import unittest

from pymice._GetTutorialData import getTutorialData

class TestGetTutorialDataBase(unittest.TestCase):
  def mockOutput(self, expectedStdout, expectedStderr):
    return self.MockOutput(self, expectedStdout, expectedStderr)

  class MockOutput(object):
    def __init__(self, testCase, expectedStdout, expectedStderr):
      self.__testCase = testCase
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
      self.__testCase.assertEqual(self.__expectedStdout, self.__stdout.getvalue())
      self.__testCase.assertEqual(self.__expectedStderr, self.__stderr.getvalue())

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
  DATASETS = {'C57_AB': ['C57_AB/2012-08-28 13.44.51.zip',
                         'C57_AB/2012-08-28 15.33.58.zip',
                         'C57_AB/2012-08-31 11.46.31.zip',
                         'C57_AB/2012-08-31 11.58.22.zip',
                         'C57_AB/timeline.ini',
                         'C57_AB/COPYING',
                         'C57_AB/LICENSE'],
              'FVB': ['FVB/2016-07-20 10.11.11.zip',
                      'FVB/COPYING',
                      'FVB/LICENSE',
                      'FVB/timeline.ini'],
              }

  def testWhenDatasetFetchedItIsSavedInTheCurrentDirectory(self):
    for name, files in self.DATASETS.items():
      getTutorialData(fetch=name)
      self.checkExist(*files)

  def testWhenDatasetFetchedNoNotificationIsDisplayed(self):
    for name in self.DATASETS:
      with self.mockOutput('', ''):
        getTutorialData(fetch=name)

  def testWhenUnknownDatasetRequestedNotificationIsDisplayed(self):
    with self.mockOutput('',
                         'Warning: unknown download requested (unknownDataset)\nAll datasets already present.\n'):
      getTutorialData(fetch='unknownDataset')


class GivenC57_ABDatasetPresent(TestGetTutorialDataBase):
  def setUp(self):
    super(GivenC57_ABDatasetPresent, self).setUp()
    getTutorialData(fetch='C57_AB')

  def testWhenTheDatasetFetchedNotificationIsDisplayed(self):
    with self.mockOutput('',
                         'C57_AB dataset already present\nAll datasets already present.\n'):
      getTutorialData(fetch='C57_AB')

  def testWhenTheDatasetFetchedWithQuietFlagNoNotificationDisplayed(self):
    with self.mockOutput('', ''):
      getTutorialData(fetch='C57_AB', quiet=True)

  def testWhenAllDatasetsFetchedMissingDatasetIsSavedInTheCurrentDirectory(self):
    getTutorialData()
    self.checkExist('demo.zip', 'COPYING', 'LICENSE')

  def testWhenAllDatasetsFetchedNotificationIsDisplayed(self):
    with self.mockOutput('',
                         'C57_AB dataset already present\n'):
      getTutorialData()


class GivenAllDatasetsPresent(TestGetTutorialDataBase):
  def setUp(self):
    super(GivenAllDatasetsPresent, self).setUp()
    getTutorialData()

  def testWhenAllDatasetsFetchedNotificationIsDisplayed(self):
    with self.mockOutput('',
                         'C57_AB dataset already present\nFVB dataset already present\ndemo dataset already present\nAll datasets already present.\n'):
      getTutorialData()