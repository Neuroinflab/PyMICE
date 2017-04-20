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

try:
  from ._TestTools import BaseTest
except (ImportError, SystemError):
  from _TestTools import BaseTest

from collections import Counter

from pymice._Analysis import Analyser, Analysis, histogram
from pymice._Ens import Ens

class TestGivenAnalyser(TestCase):
  DATA = [1, 2, 3]
  RESULT = {'min': 1,
            'max': 3,
            'span': 2}

  def min(self, objects):
    self.callCounter['min'] += 1
    return min(objects)

  def max(self, objects):
    self.callCounter['max'] += 1
    return max(objects)

  def span(self, result, objects):
    self.callCounter['span'] += 1
    return result.max - result.min

  def setUp(self):
    self.callCounter = Counter()
    self.analyser = Analyser(**{name: getattr(self, name)
                                for name in self.RESULT})

  def testResultHasAllAnalyses(self):
    self.assertEqual(self.RESULT,
                     self.analyser(self.DATA))

  def testResultIsEns(self):
    self.assertIsInstance(self.analyser(self.DATA),
                          Ens)

  def testEveryAnalyserCalledOnce(self):
    self.analyser(self.DATA)
    for name in self.RESULT:
      self.checkCalledOnce(name)

  def checkCalledOnce(self, name):
    self.assertEqual(1, self.numberOfCallsTo(name), name)

  def numberOfCallsTo(self, name):
    return self.callCounter[name]


class TestGivenPreprocessingAnalyser(TestGivenAnalyser):
  RESULT = {'min': 1,
            'max': 9,
            'span': 8}

  def preprocess(self, objects):
    self.callCounter['preprocess'] += 1
    return [o ** 2 for o in objects]

  def setUp(self):
    self.callCounter = Counter()
    self.analyser = Analyser(self.preprocess,
                             **{name: getattr(self, name)
                                for name in self.RESULT})

  def testPreprocessorCalledOnce(self):
    self.analyser(self.DATA)
    self.checkCalledOnce('preprocess')


class TestMisbehavingAnalyser(TestCase):
  def testCircularDependencyError(self):
    analyser = Analyser(res=lambda x, y: x.res)
    with self.assertRaises(Analyser.Result.CircularDependencyError):
      analyser([])

  def testUnknownDependencyError(self):
    analyser = Analyser(res=lambda x, y: x.unknown)
    with self.assertRaises(Analyser.Result.UnknownDependencyError):
      analyser([])

  def testReadOnlyError(self):
    def misbehave(result, data):
      result.res = 666
      return 666

    analyser = Analyser(misbehave=misbehave)
    with self.assertRaises(Analyser.Result.ReadOnlyError):
      analyser([])

  def testAnalyserRaisingTypeError(self):
    def misbehave(arg):
      raise TypeError('misbehave')

    analyser = Analyser(misbehave=misbehave)
    try:
      analyser([])

    except TypeError as e:
      self.assertEqual('misbehave', e.args[0])

    else:
      self.fail('No exception raised')

  def testUnknownDependencyErrorContainsDependencyName(self):
    analyser = Analyser(res=lambda x, y: x.unknown)
    try:
      analyser([])

    except Analyser.Result.UnknownDependencyError as e:
      self.assertEqual('unknown', e.args[0])

    else:
      self.fail('No exception raised')


class TestAnalyser(BaseTest):
  def testCircularDependencyErrorIsRuntimeError(self):
    self.checkIsSubclass(Analyser.Result.CircularDependencyError,
                         RuntimeError)

  def testUnknownDependencyErrorIsRuntimeError(self):
    self.checkIsSubclass(Analyser.Result.UnknownDependencyError,
                         RuntimeError)

  def testReadOnlyErrorIsTypeError(self):
    self.checkIsSubclass(Analyser.Result.ReadOnlyError,
                         TypeError)


class TestAnalysis(TestGivenAnalyser):
  class AnalysisClass(Analysis):
    def __init__(self):
      self.callCounter = Counter()
      super(TestAnalysis.AnalysisClass, self).__init__()

    @Analysis.report
    def max(self, data):
      self.callCounter['max'] += 1
      return max(data)

    @Analysis.report
    def min(self, data):
      self.callCounter['min'] += 1
      return min(data)

    @Analysis.report
    def span(self, results, data):
      self.callCounter['span'] += 1
      return results.max - results.min

  def setUp(self):
    self.analyser = self.AnalysisClass()

  def numberOfCallsTo(self, name):
    return self.analyser.callCounter[name]

  def testIsAnalyser(self):
    self.assertIsInstance(self.analyser,
                          Analyser)


class TestAnalysisWithPreprocessor(TestAnalysis):
  RESULT = {'min': 1,
            'max': 9,
            'span': 8}

  class AnalysisClass(TestAnalysis.AnalysisClass):
    def preprocess(self, data):
      self.callCounter['preprocess'] += 1
      return [x ** 2 for x in data]

  def testPreprocessorCalledOnce(self):
    self.analyser(self.DATA)
    self.checkCalledOnce('preprocess')


class TestHistogram(TestCase):
  def testEmptyOneBinHistogram(self):
    self.checkHistogram([0],
                        [], [0, 1])

  def testOneElementOneBinHistogram(self):
    self.checkHistogram([1],
                        [0.5], [0, 1])

  def testOneElementAtLowerBoundaryOfOneBinHistogram(self):
    self.checkHistogram([1],
                        [0], [0, 1])

  def testOneElementBelowLowerBoundaryOfOneBinHistogram(self):
    self.checkHistogram([0],
                        [-1], [0, 1])

  def testOneElementAtUpperBoundaryOfOneBinHistogram(self):
    self.checkHistogram([0],
                        [1], [0, 1])

  def testOneElementOverUpperBoundaryOfOneBinHistogram(self):
    self.checkHistogram([0],
                        [2], [0, 1])

  def testOneElementTwoBinHistogram(self):
    self.checkHistogram([0, 1],
                        [1.5], [0, 1, 2])

  def testTwoElementsTwoBinHistogram(self):
    self.checkHistogram([1, 1],
                        [0.5, 1], [0, 1, 2])

  def testNonNumericElements(self):
    self.checkHistogram([1, 2, 3, 0],
                        ['auto', 'bus', 'b', 'car', 'dupa', 'ciasto', 'cent'],
                        ['a', 'b', 'c', 'cz', 'd'])

  def testUnorderedBinsRaiseValueError(self):
    with self.assertRaises(ValueError):
      histogram([], bins=[1, 3, 2])

  def checkHistogram(self, result, values, bins):
    self.assertEqual(result,
                     histogram(values, bins=bins))

