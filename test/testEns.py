import collections
import unittest

from pymice._Ens import Ens

class GivenEnsBase(unittest.TestCase):
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
    yieldCounter = collections.Counter()
    for attribute in self.record:
      yieldCounter[attribute] += 1

    self.assertEqual(collections.Counter(k for (k, v) in self.ATTRS.items() if v is not None),
                     yieldCounter)

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
                       Ens.map(self.record, str))

  def checkEnsEqual(self, reference, ens):
    self.assertEqual(self.__ensToDict(reference),
                     self.__ensToDict(ens))

  def __ensToDict(self, ens):
    return dict((k, ens[k]) for k in ens if ens[k] is not None)


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


class TestEnsInitialization(unittest.TestCase):
  def testHasAttributeWhenInitializedWithDict(self):
    self.assertEqual(123,
                     Ens({'attr': 123}).attr)

  def testHasAttributeWhenInitializedWithDataRecord(self):
    self.assertEqual(123,
                     Ens(Ens(attr=123)).attr)

  def testRaisesAmbiguousInitializationErrorWhenInitializedAmbiguously(self):
    with self.assertRaises(Ens.AmbiguousInitializationError):
      Ens({'attr': 123}, attr=42)

