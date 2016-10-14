from unittest import TestCase

from pymice._Analysis import Aggregator
from pymice._Ens import Ens


class TestAggregatorBase(TestCase):
  def setUp(self):
    self.getAttributeOrSkipTheTest('aggregator')

  def getAttributeOrSkipTheTest(self, name):
    try:
      return getattr(self, name)

    except AttributeError:
      self.skipTest('{} sttribute required for test missing'.format(name))

  def testEmptySequence(self):
    self.assertEqual(self.getAttributeOrSkipTheTest('EMPTY_SEQUENCE_RESULT'),
                     self.aggregator([]))

  def testNumberSequence(self):
    self.assertEqual(self.getAttributeOrSkipTheTest('NUMBER_SEQUENCE_RESULT'),
                     self.aggregator([2, 1, 2]))


class TestGivenAggregator(TestAggregatorBase):
  def setUp(self):
    self.aggregator = Aggregator(**self.getAttributeOrSkipTheTest('AGGREGATOR_PARAMETERS'))


class GivenAggregateWithNoArguments(TestGivenAggregator):
  AGGREGATOR_PARAMETERS = {}
  EMPTY_SEQUENCE_RESULT = Ens()
  NUMBER_SEQUENCE_RESULT = Ens({1: [1], 2: [2, 2]})


class GivenAggregateWithCallableGetKey(GivenAggregateWithNoArguments):
  AGGREGATOR_PARAMETERS = {'getKey': str}
  NUMBER_SEQUENCE_RESULT = Ens({'1': [1], '2': [2, 2]})


class GivenAggregateWithStringGetKey(GivenAggregateWithNoArguments):
  AGGREGATOR_PARAMETERS = {'getKey': '__class__.__name__'}
  NUMBER_SEQUENCE_RESULT = Ens({'int': [2, 1, 2]})


class GivenAggregateWithAggregateFunction(GivenAggregateWithNoArguments):
  AGGREGATOR_PARAMETERS = {'aggregateFunction': sum}
  NUMBER_SEQUENCE_RESULT = Ens({1: 1, 2: 4})


class GivenAggregateWithRequiredKeys(TestGivenAggregator):
  AGGREGATOR_PARAMETERS = {'requiredKeys': ['a', 'b']}
  EMPTY_SEQUENCE_RESULT = Ens(a=[], b=[])
  NUMBER_SEQUENCE_RESULT = Ens({1: [1], 2: [2, 2], 'a': [], 'b': []})


class GivenEmptyAggregatorAsClassAttribute(TestAggregatorBase):
  aggregator = Aggregator()
  EMPTY_SEQUENCE_RESULT = Ens()
  NUMBER_SEQUENCE_RESULT = Ens({1: [1], 2: [2, 2]})


class GivenAggregatorExtendedWithDecoratorGetKey(GivenEmptyAggregatorAsClassAttribute):
  aggregator = Aggregator()
  NUMBER_SEQUENCE_RESULT = Ens({'1': [1], '2': [2, 2]})

  toStr = str

  @aggregator.getKey
  def getKey(self, obj):
    return self.toStr(obj)


class GivenAggregatorExtendedWithDecoratorAggregateFunction(GivenEmptyAggregatorAsClassAttribute):
  aggregator = Aggregator()
  NUMBER_SEQUENCE_RESULT = Ens({1: 1, 2: 4})

  process = sum

  @aggregator.aggregateFunction
  def aggregateFunction(self, obj):
    return self.process(obj)


class GivenAggregatorWithRequiredKeysAsClassAttribute(TestAggregatorBase):
  aggregator = Aggregator(requiredKeys=['a', 'b'])
  EMPTY_SEQUENCE_RESULT = Ens(a=[], b=[])
  NUMBER_SEQUENCE_RESULT = Ens({1: [1], 2: [2, 2], 'a': [], 'b': []})