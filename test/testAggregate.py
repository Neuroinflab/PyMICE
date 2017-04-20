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