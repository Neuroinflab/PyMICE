from unittest import TestCase, skip

try:
  from ._TestTools import BaseTest
except (ImportError, SystemError):
  from _TestTools import BaseTest

from collections import Counter

from pymice._Analysis import Analyser, Analysis
from pymice._Ens import Ens

class TestGivenAnalyser(TestCase):
  DATA = [1, 2, 3]
  RESULTS = {'min': 1,
             'max': 3,
             'span': 2}

  def min(self, objects):
    return min(objects)

  def max(self, objects):
    return max(objects)

  def span(self, result, objects):
    return result.max - result.min

  def setUp(self):
    self.analyser = Analyser(**{name: getattr(self, name)
                                for name in self.RESULTS})

  def testResultHasAllAnalyses(self):
    self.checkResult(self.RESULTS,
                     self.analyser(self.DATA))

  def testResultIsEns(self):
    self.assertIsInstance(self.analyser(self.DATA),
                          Ens)

  def testResultHasNoExtraAttributes(self):
    result = self.analyser(self.DATA)
    self.assertEqual(sorted(self.RESULTS),
                     sorted(dir(result)))

  def checkResult(self, expected, result):
    for name, value in expected.items():
      self.assertEqual(value,
                       getattr(result, name))


class TestAnalyserLaziness(TestGivenAnalyser):
  def setUp(self):
    self.callCounter = Counter()
    self.analyser = Analyser(**{name: self.getMock(getattr(self, name))
                                for name in self.RESULTS})

  def getMock(self, analyser):
    def increaseCallCounterAfterSuccessfulCall(*args):
      result = analyser(*args)
      self.callCounter[analyser.__name__] += 1
      return result

    return increaseCallCounterAfterSuccessfulCall

  def testEveryAnalyserCalledOnce(self):
    self.analyser([1])
    for name in self.RESULTS:
      self.assertEqual(1, self.callCounter[name], name)


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
    @Analysis.report
    def max(self, data):
      return max(data)

    @Analysis.report
    def min(self, data):
      return min(data)

    @Analysis.report
    def span(self, results, data):
      return results.max - results.min

  def setUp(self):
    self.analyser = self.AnalysisClass()

  def testIsAnalyser(self):
    self.assertIsInstance(self.analyser,
                          Analyser)

