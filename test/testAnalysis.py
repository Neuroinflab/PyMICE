from unittest import TestCase, skip

from pymice._Analysis import Analysis
from pymice._Ens import Ens

class TestGivenAnalyser(TestCase):
  ANALYSES = {'min': min,
              'max': max}

  def setUp(self):
    self.analyser = Analysis(**self.ANALYSES)

  def testResultHasAllAnalyses(self):
    self.checkResult({'min': 1,
                      'max': 2},
                     self.analyser([1, 2]))

  def testResultIsEns(self):
    self.assertIsInstance(self.analyser([1]),
                          Ens)

  def testResultHasNoExtraAttributes(self):
    result = self.analyser([1])
    self.assertEqual(sorted(self.ANALYSES),
                     sorted(dir(result)))

  def checkResult(self, expected, result):
    for name, value in expected.items():
      self.assertEqual(value,
                       getattr(result, name))

