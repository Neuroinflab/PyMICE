#!/usr/bin/env python
# encoding: utf-8
###############################################################################
#                                                                             #
#    PyMICE library                                                           #
#                                                                             #
#    Copyright (C) 2015-2019 Jakub M. Dzik a.k.a. Kowalski, S. Łęski          #
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

import sys
import unittest

from collections import namedtuple
from io import StringIO

from pymice._ICDataLoader import (_FileCollectionLoader,
                                  _FileCollectionLoader_v_Version1,
                                  _FileCollectionLoader_v_Version_2_2,
                                  _FileCollectionLoader_v_IntelliCage_Plus_3)
from pymice._ICData import Animal

try:
  from ._TestTools import BaseTest

except (SystemError, ValueError):
  from _TestTools import BaseTest

if sys.version_info >= (3, 0):
  unicode = str

_A = namedtuple('_A', ('Name', 'Tag', 'Sex', 'Notes'))


class Test_FileCollectionLoaderBase(BaseTest):
  ANIMALS_PATH = 'Animals.txt'
  DATA_DESCRIPTOR_PATH = 'DataDescriptor.xml'

  class DictionaryFileCollection(dict):
    class StringWrapper(object):
      def __init__(self, data):
        self._data = StringIO(data)

      def __enter__(self):
        try:
          return self._data.__enter__()

        except AttributeError:
          return self._data

      def __exit__(self, exc_type, exc_val, exc_tb):
        try:
          return self._data.__exit__(exc_type, exc_val, exc_tb)

        except AttributeError:
          pass

      def __getattr__(self, name):
        return getattr(self._data, name)

      def __iter__(self):
        return iter(self._data)

    def open(self, path, mode='r'):
      return self.StringWrapper(unicode(self[path]))

  def setUp(self):
    super(Test_FileCollectionLoaderBase, self).setUp()
    if self._isAbstractClassObject():
      self.skipTest('Tests declared in abstract class')
      return # False

    self._setUpFileCollection()
    self._loader = _FileCollectionLoader.getLoader(self._fileCollection)
    # return True

  def _isAbstractClassObject(self):
    if not hasattr(self, 'CLASS'):
      return True

    return not self._canSetUpFileCollection()

  def _canSetUpFileCollection(self):
    for attrName in ['DATA_DESCRIPTOR',
                     'ANIMALS',
                     ]:
      for attrSuffix in ['', '_PATH']:
        if not hasattr(self, attrName + attrSuffix):
          return False

    return True

  def _setUpFileCollection(self):
    self._fileCollection = self.DictionaryFileCollection(
      {
        self.DATA_DESCRIPTOR_PATH: self.DATA_DESCRIPTOR,
        self.ANIMALS_PATH: self._getAnimalsFile(),
      })

  def _getAnimalsFile(self):
    return '\n'.join(['\t'.join(self.ANIMALS_FIELDS)] \
                     + ['{0.Name}\t{0.Tag}\t{0.Sex}\t\t'.format(a)
                        for a in self._ANIMALS]) \
           + '\n'

  def testClassIsSubclassOfNewFileCollectionLoader(self):
    self.assertTrue(issubclass(self.CLASS, _FileCollectionLoader))

  def testGetLoaderReturnsClassInstance(self):
    self.assertIsInstance(self._loader, self.CLASS)

  def testLoaderHasProperVersionAttribute(self):
    self.assertEqual(self.VERSION,
                     self._loader.version)

  @property
  def ANIMALS(self):
    return frozenset(Animal.fromRow(*a) for a in self._ANIMALS)

  def testGetMice(self):
    mice = self._loader.getMice()
    self.assertEqual(self.ANIMALS,
                     mice)
    self.assertIsInstance(mice, frozenset)


class Test_FileCollectionLoader_v_Version1(Test_FileCollectionLoaderBase):
  CLASS = _FileCollectionLoader_v_Version1
  VERSION = 'Version1'

  DATA_DESCRIPTOR = """<?xml version="1.0" encoding="utf-8"?>
<DataDescriptor xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xsd="http://www.w3.org/2001/XMLSchema">
  <Version>Version1</Version>
</DataDescriptor>"""

  ANIMALS_FIELDS = ['Name',
                    'Tag',
                    'Sex',
                    'Group',
                    'Notes']


class Test_FileCollectionLoader_v_Version_2_2(Test_FileCollectionLoaderBase):
  CLASS = _FileCollectionLoader_v_Version_2_2
  VERSION = 'Version_2_2'

  DATA_DESCRIPTOR = """<?xml version="1.0" encoding="utf-8"?>
<DataDescriptor xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xsd="http://www.w3.org/2001/XMLSchema">
  <Version>Version_2_2</Version>
</DataDescriptor>"""

  ANIMALS_FIELDS = ['AnimalName',
                    'AnimalTag',
                    'Sex',
                    'GroupName',
                    'AnimalNotes']


class Test_FileCollectionLoader_v_IntelliCage_Plus_3(Test_FileCollectionLoaderBase):
  CLASS = _FileCollectionLoader_v_IntelliCage_Plus_3
  VERSION = 'IntelliCage_Plus_3'

  DATA_DESCRIPTOR = """<?xml version="1.0" encoding="utf-8"?>
<DataDescriptor xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xsd="http://www.w3.org/2001/XMLSchema">
  <Version>IntelliCage_Plus_3</Version>
</DataDescriptor>"""

  ANIMALS_FIELDS = ['AnimalName',
                    'AnimalTag',
                    'Sex',
                    'GroupName',
                    'AnimalNotes']


class TestNewFileCollectionLoader_givenNoAnimals(Test_FileCollectionLoaderBase):
  _ANIMALS = []


class TestNewFileCollectionLoader_givenOneAnimalNoNotes(Test_FileCollectionLoaderBase):
  _ANIMALS = [_A('Mickey', '42', 'Male', ''),
              ]


def load_tests(loader, standard_tests, pattern):
  for cls in [Test_FileCollectionLoader_v_Version1,
              Test_FileCollectionLoader_v_Version_2_2,
              Test_FileCollectionLoader_v_IntelliCage_Plus_3,
              ]:
    for animalCls in [TestNewFileCollectionLoader_givenNoAnimals,
                      TestNewFileCollectionLoader_givenOneAnimalNoNotes,
                      ]:
      standard_tests.addTest(loader.loadTestsFromTestCase(
        type(cls.__name__ + '_Given' + animalCls.__name__[33:] + '_DD',
             (cls, animalCls),
             {})))
  return standard_tests

if __name__ == '__main__':
  unittest.main()