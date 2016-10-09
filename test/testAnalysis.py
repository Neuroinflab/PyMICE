from unittest import TestCase, skip

try:
  from ._TestTools import BaseTest
except (ImportError, SystemError):
  from _TestTools import BaseTest

from collections import Counter

from pymice._Analysis import Analysis
from pymice._Ens import Ens

class TestGivenAnalyser(TestCase):
  ANALYSERS = ['min', 'max', 'span']

  def min(self, objects):
    return min(objects)

  def max(self, objects):
    return max(objects)

  def span(self, objects):
    return objects.result.max - objects.result.min

  def setUp(self):
    self.analyser = Analysis(**{name: getattr(self, name)
                                for name in self.ANALYSERS})

  def testResultHasAllAnalyses(self):
    self.checkResult({'min': 1,
                      'max': 3,
                      'span': 2},
                     self.analyser([1, 2, 3]))

  def testResultIsEns(self):
    self.assertIsInstance(self.analyser([1]),
                          Ens)

  def testResultHasNoExtraAttributes(self):
    result = self.analyser([1])
    self.assertEqual(sorted(self.ANALYSERS),
                     sorted(dir(result)))

  def checkResult(self, expected, result):
    for name, value in expected.items():
      self.assertEqual(value,
                       getattr(result, name))


class TestAnalyserLaziness(TestGivenAnalyser):
  def setUp(self):
    self.callCounter = Counter()
    self.analyser = Analysis(**{name: self.getMock(getattr(self, name))
                                for name in self.ANALYSERS})

  def getMock(self, analyser):
    def mockAnalyser(objects):
      self.callCounter[analyser.__name__] += 1
      return analyser(objects)

    return mockAnalyser

  def testEveryAnalyserCalledOnce(self):
    self.analyser([1])
    for name in self.ANALYSERS:
      self.assertEqual(1, self.callCounter[name], name)


class TestMisbehavingAnalyser(TestCase):
  def testCircularDependencyError(self):
    analyser = Analysis(res=lambda x: x.result.res)
    with self.assertRaises(Analysis.Results.CircularDependencyError):
      analyser([])

  def testUnknownDependencyError(self):
    analyser = Analysis(res=lambda x: x.result.unknown)
    with self.assertRaises(Analysis.Results.UnknownDependencyError):
      analyser([])


class TestAnalyser(BaseTest):
  def testCircularDependencyErrorIsRuntimeError(self):
    self.checkIsSubclass(Analysis.Results.CircularDependencyError,
                         RuntimeError)

  def testUnknownDependencyErrorIsRuntimeError(self):
    self.checkIsSubclass(Analysis.Results.UnknownDependencyError,
                         RuntimeError)