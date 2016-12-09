from unittest import TestCase

from pymice._Results import lazyAttribute

class TestLazyAttribute(TestCase):
  class TestObject(object):
    def __init__(self, valueGenerator):
      self.getAttributeValue = valueGenerator

    @lazyAttribute
    def dynamicAttribute(self):
      return self.getAttributeValue()

  def functionGeneratingTheValue(self):
    self.functionCall += 1
    return 1337

  def setUp(self):
    self.obj = self.TestObject(self.functionGeneratingTheValue)
    self.functionCall = 0

  def testAttributeValue(self):
    self.assertEqual(1337, self.obj.dynamicAttribute)

  def testAttributeLaziness(self):
    self.assertEqual(0, self.functionCall)
    self.obj.dynamicAttribute
    self.assertEqual(1, self.functionCall)

  def testAttributeCaching(self):
    self.assertEqual(0, self.functionCall)
    self.obj.dynamicAttribute
    self.assertEqual(1, self.functionCall)
    self.assertEqual(1337, self.obj.dynamicAttribute)
    self.assertEqual(1, self.functionCall)
