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
    self.checkAggregationResult('EMPTY_SEQUENCE_RESULT', [])

  def testNumberSequence(self):
    self.checkAggregationResult('NUMBER_SEQUENCE_RESULT', [2, 1, 2])

  def checkAggregationResult(self, resultAttribute, sequence):
    result = self.getAttributeOrSkipTheTest(resultAttribute)
    self.checkAggregator(result, sequence)
    self.checkAggregateStaticMethod(result, sequence)

  def checkAggregateStaticMethod(self, result, sequence):
    try:
      params = self.AGGREGATOR_PARAMETERS

    except AttributeError:
      pass

    else:
      self.assertEqual(result,
                       Aggregator.aggregate(sequence,
                                            **params))

  def checkAggregator(self, result, sequence):
    self.assertEqual(result,
                     self.aggregator(sequence))


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