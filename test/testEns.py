import collections
import unittest
from unittest import TestCase

from pymice._Ens import Ens


class TestEnsBase(TestCase):
  def checkEnsEqual(self, reference, ens):
    self.assertEqual(self.__ensToDict(reference),
                     self.__ensToDict(ens))

  def __ensToDict(self, ens):
    return dict((k, ens[k]) for k in ens if ens[k] is not None)


class GivenEnsBase(TestEnsBase):
  ATTRS = None

  def setUp(self):
    if self.ATTRS is None:
      self.skipTest('Tests declared in abstract class')

    self.record = Ens(**self.ATTRS)

  def testHasAllAttributes(self):
    for attribute, value in self.ATTRS.items():
      self.assertEqual(value,
                       getattr(self.record, attribute))

  def testHasAllItems(self):
    for key, value in self.ATTRS.items():
      self.assertEqual(value,
                       self.record[key])

  def testYieldsAllNotNoneAttributesOnceWhenIterated(self):
    self.checkAllNonNoneAttributesYieldedOnce(self.record)

  def testDirOutputContainsAllNotNoneAttributesOnce(self):
    self.checkAllNonNoneAttributesYieldedOnce(dir(self.record))

  def checkAllNonNoneAttributesYieldedOnce(self, iterable):
    self.assertEqual(self.countKeysOfNonNoneValues(self.ATTRS),
                     self.countItemsInIterable(iterable))

  def countKeysOfNonNoneValues(self, dictionary):
    return collections.Counter(k for (k, v) in dictionary.items()
                               if v is not None)

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
      delattr(self.record, attrname)

  def testRaisesReadOnlyErrorWhenItemDeleted(self):
    for key in self.ATTRS:
      self.checkRaisesReadOnlyErrorWhenItemDeleted(key)

  def checkRaisesReadOnlyErrorWhenItemDeleted(self, key):
    with self.assertRaises(Ens.ReadOnlyError):
      del self.record[key]

  def testMappedChangesNonNoneAttributes(self):
    self.checkEnsEqual(dict((k, str(v)) for (k, v) in self.ATTRS.items() if v is not None),
                       Ens.map(str, self.record))


class GivenEmptyEns(GivenEnsBase):
  ATTRS = {}

  def testReturnsNoneWhenAttributeAccessed(self):
    self.assertIsNone(self.record.anyAttr)

  def testReturnsNoneWhenItemAccessed(self):
    self.assertIsNone(self.record["anyAttr"])

  def testRaisesReadOnlyErrorWhenAttributeAssigned(self):
    with self.assertRaises(Ens.ReadOnlyError):
      self.record.anyAttr = 123

  def testRaisesReadOnlyErrorWhenItemAssigned(self):
    with self.assertRaises(Ens.ReadOnlyError):
      self.record["anyAttr"] = 123

  def testMapAttributeIsNone(self):
    self.assertIsNone(self.record.map)


class GivenEnsOfOneAttribute(GivenEnsBase):
  ATTRS = {'attr': 123}


class GivenEnsOfManyAttributes(GivenEnsBase):
  ATTRS = {'attr1': 1337,
           'attr2': 42,
           }

class GivenEnsInitizedWithNoneAttribute(GivenEnsBase):
  ATTRS = {'attr1': 1337,
           'attr2': 42,
           'noneAttr': None,
           }

class GivenEnsInitizedWithMapAttribute(GivenEnsBase):
  ATTRS = {'attr1': 1337,
           'attr2': 42,
           'map': 666,
           }


class TestEns(TestEnsBase):
  def testHasAttributeWhenInitializedWithDict(self):
    self.assertEqual(123,
                     Ens({'attr': 123}).attr)

  def testHasAttributeWhenInitializedWithDataRecord(self):
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
