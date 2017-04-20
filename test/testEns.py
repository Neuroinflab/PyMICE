#!/usr/bin/env python
# encoding: utf-8
###############################################################################
#                                                                             #
#    PyMICE library                                                           #
#                                                                             #
#    Copyright (C) 2016-2017 Jakub M. Dzik a.k.a. Kowalski (Laboratory of     #
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
from unittest import TestCase, skip

try:
  from ._TestTools import BaseTest
except (ImportError, SystemError):
  from _TestTools import BaseTest

from pymice._Ens import Ens


class TestEnsBase(BaseTest):
  def checkEnsEqual(self, reference, ens):
    self.assertEqual(self.__ensToDict(reference),
                     self.__ensToDict(ens))

  def __ensToDict(self, ens):
    return dict((k, ens[k]) for k in ens)



class GivenEnsBase(TestEnsBase):
  ATTRS = None

  def setUp(self):
    if self.ATTRS is None:
      self.skipTest('Tests declared in abstract class')

    self.ens = Ens(**self.ATTRS)

  def testHasAllAttributes(self):
    for attribute, value in self.ATTRS.items():
      self.assertEqual(value,
                       getattr(self.ens, attribute))

  def testHasAllItems(self):
    for key, value in self.ATTRS.items():
      self.assertEqual(value,
                       self.ens[key])

  def testContainsAllItems(self):
    for key in self.ATTRS:
      self.assertIn(key, self.ens)
      self.assertTrue(key in self.ens)
      self.assertFalse(key not in self.ens)

  def testYieldsAllAttributesOnceWhenIterated(self):
    self.checkAllAttributesYieldedOnce(self.ens)

  def testDirOutputContainsAllAttributesOnce(self):
    self.checkAllAttributesYieldedOnce(dir(self.ens))

  def checkAllAttributesYieldedOnce(self, iterable):
    self.assertEqual(self.countKeysOfValues(self.ATTRS),
                     self.countItemsInIterable(iterable))

  def countKeysOfValues(self, dictionary):
    return collections.Counter(k for (k, v) in dictionary.items())

  def countItemsInIterable(self, iterable):
    yieldCounter = collections.Counter()
    for attribute in iterable:
      yieldCounter[attribute] += 1

    return yieldCounter

  def testRaisesReadOnlyErrorWhenAttributeDeleted(self):
    for attrname in self.ATTRS:
      self.checkRaisesReadOnlyErrorWhenAttributeDeleted(attrname)

  def checkRaisesReadOnlyErrorWhenAttributeDeleted(self, attrname):
    with self.assertRaises(Ens.ReadOnlyError):
      delattr(self.ens, attrname)

  def testRaisesReadOnlyErrorWhenItemDeleted(self):
    for key in self.ATTRS:
      self.checkRaisesReadOnlyErrorWhenItemDeleted(key)

  def checkRaisesReadOnlyErrorWhenItemDeleted(self, key):
    with self.assertRaises(Ens.ReadOnlyError):
      del self.ens[key]

  def testMappedChangesAttributes(self):
    self.checkEnsEqual(dict((k, str(v)) for (k, v) in self.ATTRS.items()),
                       Ens.map(str, self.ens))

  def checkRepr(self, representation):
    self.assertEqual(representation, repr(self.ens))

  def testEqualEnsOfSameMembers(self):
    other = Ens(self.ATTRS)
    self.assertTrue(self.ens == other)
    self.assertFalse(self.ens != other)

  def testNotEqualEnsOfDifferentMembers(self):
    other = Ens(self.ens, otherMember='a')
    self.assertTrue(self.ens != other)
    self.assertFalse(self.ens == other)

  def testEqualDictOfSameMembers(self):
    self.assertTrue(self.ens == self.ATTRS)
    self.assertFalse(self.ens != self.ATTRS)
    self.assertTrue(self.ATTRS == self.ens)
    self.assertFalse(self.ATTRS != self.ens)


  def testNotEqualDictOfDifferentMembers(self):
    other = {'otherMember': 'a'}
    self.assertTrue(self.ens != other)
    self.assertFalse(self.ens == other)
    self.assertTrue(other != self.ens)
    self.assertFalse(other == self.ens)


class GivenEmptyEns(GivenEnsBase):
  ATTRS = {}

  def testRaisesUndefinedAttributeErrorWhenAttributeAccessed(self):
    with self.assertRaises(Ens.UndefinedAttributeError):
      self.ens.anyAttr

  def testUndefinedAttributeErrorContainsNameOfAttribute(self):
    try:
      self.ens.anyAttr

    except Ens.UndefinedAttributeError as e:
      self.assertEqual('anyAttr',
                       e.args[0])

  def testRaisesUndefinedKeyErrorWhenItemAccessed(self):
    with self.assertRaises(Ens.UndefinedKeyError):
      self.ens["anyAttr"]

  def testUndefinedKeyErrorContainsNameOfKey(self):
    try:
      self.ens['anyAttr']

    except Ens.UndefinedKeyError as e:
      self.assertEqual('anyAttr',
                       e.args[0])

  def testDoesNotContainAnyItem(self):
    self.assertNotIn('anyAttr', self.ens)
    self.assertFalse('anyAttr' in self.ens)
    self.assertTrue('anyAttr' not in self.ens)

  def testRaisesReadOnlyErrorWhenAttributeAssigned(self):
    with self.assertRaises(Ens.ReadOnlyError):
      self.ens.anyAttr = 123

  def testRaisesReadOnlyErrorWhenItemAssigned(self):
    with self.assertRaises(Ens.ReadOnlyError):
      self.ens["anyAttr"] = 123

  def testMapAttributeDoesNotExist(self):
    with self.assertRaises(Ens.UndefinedAttributeError):
      self.ens.map

  def testAsMappingAttributeDoesNotExist(self):
    with self.assertRaises(Ens.UndefinedAttributeError):
      self.ens.asMapping

  def testRepr(self):
      self.checkRepr('Ens({})')


class GivenEnsOfOneAttribute(GivenEnsBase):
  ATTRS = {'attr': 123}

  def testRepr(self):
    self.checkRepr('Ens({{{!r}: 123}})'.format('attr'))

class GivenEnsOfManyAttributes(GivenEnsBase):
  ATTRS = {'attr1': 1337,
           'attr2': 42,
           }

  def testRepr(self):
    self.checkRepr('Ens({{{!r}: 1337, {!r}: 42}})'.format('attr1', 'attr2'))


class GivenEnsInitializedWithNoneAttribute(GivenEnsBase):
  ATTRS = {'attr1': 1337,
           'attr2': 42,
           'noneAttr': None,
           }

  def testRepr(self):
    self.checkRepr('Ens({{{!r}: 1337, {!r}: 42, {!r}: None}})'.format('attr1', 'attr2', 'noneAttr'))


class GivenEnsInitializedWithStrAttributeValue(GivenEnsBase):
  ATTRS = {'attr1': 1337,
           'attr2': 42,
           'strAttr': 'str',
           }

  def testRepr(self):
    self.checkRepr('Ens({{{!r}: 1337, {!r}: 42, {!r}: {!r}}})'.format('attr1', 'attr2', 'strAttr', 'str'))


class GivenEnsInitializedWithMapAttribute(GivenEnsBase):
  ATTRS = {'attr1': 1337,
           'attr2': 42,
           'map': 666,
           }

  def testRepr(self):
    self.checkRepr('Ens({{{!r}: 1337, {!r}: 42, {!r}: 666}})'.format('attr1', 'attr2', 'map'))


class GivenEnsInitializedWithDictAttribute(GivenEnsBase):
  ATTRS = {'attr1': 1337,
           'attr2': 42,
           '__dict__': 666,
           }


class GivenEnsInitializedWithNumericAttribute(GivenEnsBase):
  ATTRS = {'attr1': 1337,
           'attr2': 42,
           666: 'numeric',
           }

  def setUp(self):
    self.ens = Ens(self.ATTRS)

  def testRepr(self):
    self.checkRepr('Ens({{{!r}: 1337, {!r}: 42, 666: {!r}}})'.format('attr1', 'attr2', 'numeric'))

  @skip('numeric attribute name is incompatible with delattr()')
  def testRaisesReadOnlyErrorWhenAttributeDeleted(self):
    pass

  @skip('numeric attribute name is incompatible with getattr()')
  def testHasAllAttributes(self):
    pass

  @skip('numeric attribute name is incompatible with dir()')
  def testDirOutputContainsAllAttributesOnce(self):
    pass


class TestEns(TestEnsBase):
  def testHasAttributeWhenInitializedWithDict(self):
    self.assertEqual(123,
                     Ens({'attr': 123}).attr)

  def testHasAttributeWhenInitializedWithEns(self):
    self.assertEqual(123,
                     Ens(Ens(attr=123)).attr)

  def testRaisesAmbiguousInitializationErrorWhenInitializedAmbiguously(self):
    with self.assertRaises(Ens.AmbiguousInitializationError):
      Ens({'attr': 123}, attr=42)

  def testMapOverMultipleEnsReturnsAggregatedEns(self):
    self.checkEnsEqual({'x': 4},
                       Ens.map(max, Ens(x=1), Ens(x=4)))

  def testMapOverMultipleEnsWithMissingValuesReturnsAggregatedEns(self):
    self.checkEnsEqual({'x': (None, 4)},
                       Ens.map(lambda a, b: (a, b), Ens(), Ens(x=4)))

  def testMapAcceptsDictsAsInput(self):
    self.checkEnsEqual({'x': '42'},
                       Ens.map(str, {'x': 42}))

  def testUndefinedKeyErrorIsKeyError(self):
    self.checkIsSubclass(Ens.UndefinedKeyError,
                         KeyError)

  def testUndefinedAttributeErrorIsAttributeError(self):
    self.checkIsSubclass(Ens.UndefinedAttributeError,
                         AttributeError)

  def testAmbiguousInitializationErrorIsValueError(self):
    self.checkIsSubclass(Ens.AmbiguousInitializationError,
                         ValueError)

  def testReadOnlyErrorIsTypeError(self):
    self.checkIsSubclass(Ens.ReadOnlyError,
                         TypeError)


class TestAsMapping(TestCase):
  ATTRS = {'answer': 42,
           'noneAttribute': None}

  def setUp(self):
    self.mapping = Ens.asMapping(Ens(self.ATTRS))

  def testHasItemsWhichTheEnsHad(self):
    for key, value in self.ATTRS.items():
      self.assertEqual(value,
                       self.mapping[key])

  def testHasKeysMethodReturningKeysDefinedInTheEns(self):
    self.assertEqual(sorted(self.ATTRS),
                     sorted(self.mapping.keys()))

  def testHasLength(self):
    self.assertEqual(len(self.ATTRS),
                     len(self.mapping))

  def testIteratesItsKeys(self):
    self.assertEqual(sorted(self.mapping.keys()),
                     sorted(self.mapping))

  def testContainsItsKeys(self):
    for key in self.mapping.keys():
      self.assertTrue(key in self.mapping)

  def testHasItemsMethodReturningKeyValuePairsOfEns(self):
    self.assertEqual(sorted(self.ATTRS.items()),
                     sorted(self.mapping.items()))