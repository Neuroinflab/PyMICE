import collections
import unittest
from unittest import TestCase

from pymice._Ens import Ens, JS


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



class TestJSBase(TestCase):
  def checkHas(self, js, **items):
    for key, value in items.items():
      self.assertEqual(value, js[key])


class TestJS(TestJSBase):
  def testCanBeInitializedWithDict(self):
    self.checkHas(JS({'a': 42}), a=42)

  def testCanBeInitializedWithManyDicts(self):
    self.checkHas(JS({'a': 42}, {'b': 1337}),
                  a=42, b=1337)

  def testCanBeInitializedWithKwargs(self):
    self.checkHas(JS(a=42), a=42)

  def testWhenInitializedKwargsOverrideDicts(self):
    self.checkHas(JS({'a': None}, a=42),
                  a=42)

  def testWhenDirCalledItDoesNotReturnNonStringItems(self):
    self.assertTrue(1 not in dir(JS({1: 2})))


class GivenEmptyJS(TestJSBase):
  def setUp(self):
    self.js = JS()

  def testWhenItemSetItCanBeAccessedAsAttribute(self):
    self.js['a'] = 42
    self.assertEqual(42, self.js.a)

  def testWhenAttributeSetItCanBeAccessedAsItem(self):
    self.js.a = 42
    self.assertEqual(42, self.js['a'])

  def testWhenAttributeAccessedRaisesAttributeError(self):
    with self.assertRaises(AttributeError):
      self.js.a

  def testWhenAttributeDeletedRaisesAttributeError(self):
    with self.assertRaises(AttributeError):
      del self.js.a

  def testWhenUpdatedWithEnsUpdatesItsAttributes(self):
    self.js.update(Ens(a=42))
    self.checkHas(self.js, a=42)

  def testWhenUpdatedWithKwargUpdatesItsAttributes(self):
    self.js.update(E=42)
    self.checkHas(self.js, E=42)


class GivenOneAttributeJS(TestJSBase):
  def setUp(self):
    self.js = JS(attribute=42)

  def testWhenDeletedAttributeAccessedRaisesAttributeError(self):
    del self.js.attribute
    with self.assertRaises(AttributeError):
      self.js.attribute


if __name__ == '__main__':
  unittest.main()