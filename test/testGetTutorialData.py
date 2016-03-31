import io
import os
import shutil
import sys
import tempfile
import unittest

from pymice._GetTutorialData import getTutorialData

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