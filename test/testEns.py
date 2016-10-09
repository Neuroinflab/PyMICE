import collections
from unittest import TestCase, skip

from pymice._Ens import Ens


class TestEnsBase(TestCase):
  def checkEnsEqual(self, reference, ens):
    self.assertEqual(self.__ensToDict(reference),
                     self.__ensToDict(ens))

  def __ensToDict(self, ens):
    return dict((k, ens[k]) for k in ens)

  def checkIsSubclass(self, subclass, superclass):
    self.assertTrue(issubclass(subclass,
                               superclass))


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


class GivenEmptyEns(GivenEnsBase):
  ATTRS = {}

  def testRaisesUndefinedAttributeErrorWhenAttributeAccessed(self):
    with self.assertRaises(Ens.UndefinedAttributeError):
      self.ens.anyAttr

  def testRaisesUndefinedKeyErrorWhenItemAccessed(self):
    with self.assertRaises(Ens.UndefinedKeyError):
      self.ens["anyAttr"]

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

class GivenEnsInitializedWithMapAttribute(GivenEnsBase):
  ATTRS = {'attr1': 1337,
           'attr2': 42,
           'map': 666,
           }

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