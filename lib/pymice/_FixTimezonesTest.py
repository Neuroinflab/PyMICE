#!/usr/bin/env python
# encoding: utf-8
###############################################################################
#                                                                             #
#    PyMICE library                                                           #
#                                                                             #
#    Copyright (C) 2012-2015 Jakub M. Kowalski, S. Łęski (Laboratory of       #
#    Neuroinformatics; Nencki Institute of Experimental Biology)              #
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

import unittest

from datetime import datetime, timedelta
import pytz

from _FixTimezones import inferTimezones, TimezonesInferrer, LatticeOrderer


utc = pytz.utc
utcDST = pytz.timezone('Etc/GMT-1')

sessionStart = datetime(2015, 7, 4, 17, 40, tzinfo=utc)
sessionEnd = datetime(2015, 7, 4, 20, 40, tzinfo=utc)
timeChange = datetime(2015, 7, 4, 18, 40, tzinfo=utc)
minute = timedelta(seconds=60)

def likeDST(time):
  return time.astimezone(utcDST).replace(tzinfo=utc)

def dateRange(start, end, step):
  time = start
  result = []
  while time < end:
    result.append(datetimeToList(time))
    time += step

  return result

def datetimeToList(time):
  return [time.year, time.month, time.day,
          time.hour, time.minute, time.second]

class TestDateRange(unittest.TestCase):
  def testEmptyRange(self):
    self.assertEqual([], dateRange(sessionStart, sessionStart, minute))

  def testOneItem(self):
    self.assertEqual(dateRange(sessionStart, sessionStart + minute, minute),
                     [[2015, 7, 4, 17, 40, 0]])

  def testMoreItems(self):
    self.assertEqual(dateRange(sessionStart, sessionStart + 2 * minute, minute),
                     [[2015, 7, 4, 17, 40, 0],
                      [2015, 7, 4, 17, 41, 0]])

def makeTestCases(start, end, step):
  naiveTimeLists = dateRange(start,end, step)
  return naiveTimeLists, [start.tzinfo] * len(naiveTimeLists)


class TestFixTimezones(unittest.TestCase):
  def testEmptyTimepointsStayEmpty(self):
    self.assertEqual(inferTimezones([], sessionStart),
                     [])
    self.assertEqual(inferTimezones([], sessionStart, sessionEnd),
                     [])
    self.assertEqual(inferTimezones([], sessionStart, sessionEnd.astimezone(utcDST)),
                     [])

  def testInSessionTimepointsGetSameTimezoneAsBothStartAndEnd(self):
    self.assertEqual(inferTimezones([[2015, 7, 4, 17, 45, 15, 0]],
                                    sessionStart, sessionEnd),
                     [utc])


    self.assertEqual(inferTimezones([[2015, 7, 4, 17, 45, 15, 0],
                                     [2015, 7, 4, 17, 56, 43, 1]],
                                    sessionStart, sessionEnd),
                     [utc, utc])

  def testInOpenSessionTimepointsGetSameTimezoneAsStart(self):
    self.assertEqual(inferTimezones([[2015, 7, 4, 17, 45, 15, 0]],
                                    sessionStart, None),
                     [utc])
    self.assertEqual(inferTimezones([[2015, 7, 4, 17, 45, 15, 0],
                                     [2015, 7, 4, 17, 56, 43, 1]],
                                    sessionStart, None),
                     [utc, utc])

  def testDetectionOfChangeToDST(self):
    timepointsUTC, timezonesUTC = makeTestCases(sessionStart, timeChange, minute)
    timepointsDST, timezonesDST = makeTestCases(timeChange.astimezone(utcDST),
                                       sessionEnd.astimezone(utcDST),
                                       minute)
    inferred = inferTimezones(timepointsUTC + timepointsDST, sessionStart, sessionEnd.astimezone(utcDST))
    self.assertEqual(inferred, timezonesUTC + timezonesDST)

    self.assertEqual(inferTimezones(timepointsUTC, sessionStart, sessionEnd.astimezone(utcDST)),
                     timezonesUTC)

    self.assertEqual(inferTimezones(timepointsDST, sessionStart, sessionEnd.astimezone(utcDST)),
                     timezonesDST)

  def testAmbigousChangeToDST(self):
    timepoints = dateRange(sessionStart + 61 * minute, sessionStart + 65 * minute, minute) +\
                 dateRange(sessionStart + 126 * minute, sessionStart + 130 * minute, minute)
    with self.assertRaises(TimezonesInferrer.TooManyIntervalsBigEnoughForTimeAdvance):
      inferTimezones(timepoints, sessionStart, sessionEnd.astimezone(utcDST))

  def testNoChangeToDST(self):
    timepoints = dateRange(sessionStart, likeDST(sessionEnd), minute)
    with self.assertRaises(TimezonesInferrer.NoIntervalsBigEnoughForTimeAdvance):
      inferTimezones(timepoints, sessionStart, sessionEnd.astimezone(utcDST))

  def testDetectionOfChangeFromDST(self):
    timepointsDST, timezonesDST = makeTestCases(sessionStart.astimezone(utcDST),
                                                timeChange.astimezone(utcDST),
                                                minute)
    timepointsUTC, timezonesUTC = makeTestCases(timeChange, sessionEnd, minute)
    inferred = inferTimezones(timepointsDST + timepointsUTC, sessionStart.astimezone(utcDST), sessionEnd)
    self.assertEqual(inferred, timezonesDST + timezonesUTC)

  def testAmbigousChangeFromDST(self):
    with self.assertRaises(TimezonesInferrer.AmbigousTimezoneChangeError):
      timepoints = dateRange(likeDST(sessionStart), sessionEnd, minute)
      inferTimezones(timepoints, sessionStart.astimezone(utcDST), sessionEnd)

    with self.assertRaises(TimezonesInferrer.AmbigousTimezoneChangeError):
      timepoints = dateRange(sessionStart - 121 * minute, sessionEnd, minute)
      inferTimezones(timepoints, sessionStart.astimezone(utcDST), sessionEnd)

    with self.assertRaises(TimezonesInferrer.AmbigousTimezoneChangeError):
      timepoints = dateRange(likeDST(sessionStart),
                             sessionEnd + 120 * minute, minute)
      inferTimezones(timepoints, sessionStart.astimezone(utcDST), sessionEnd)

    with self.assertRaises(TimezonesInferrer.AmbigousTimezoneChangeError):
      start = likeDST(sessionStart)
      timepoints = dateRange(start, start + 90*minute, minute) +\
                   dateRange(start + 40*minute, start + 110*minute, minute) +\
                   dateRange(start + 60*minute, sessionEnd, minute)
      inferTimezones(timepoints, sessionStart.astimezone(utcDST), sessionEnd)


class TestLatticeOrderer(unittest.TestCase):
  def setUp(self):
    self.orderer = LatticeOrderer()

  def tearDown(self):
    del self.orderer

  def testEmptyStaysEmpty(self):
    self.compareOrderTo([])

  def testSimpleOrder(self):
    for node in map(LatticeOrderer.Node, [[3], [1], [2]]):
      self.orderer.addNodes(node)

    self.compareOrderTo([[1], [2], [3]])

  def testSimpleLatticeOrder(self):
    b = LatticeOrderer.Node([1])
    a = LatticeOrderer.Node([2]).markLessThan(b)
    self.orderer.addNodes(a, b)
    self.compareOrderTo([[2], [1]])

  def testComplexLatticeOrder(self):
    d = LatticeOrderer.Node([0])
    b = LatticeOrderer.Node([2]).markLessThan(d)
    c = LatticeOrderer.Node([1]).markLessThan(d)
    a = LatticeOrderer.Node([3]).markLessThan(b).markLessThan(c)
    self.orderer.addNodes(a, b, c, d)
    self.compareOrderTo([[3], [1], [2], [0]])


    f = LatticeOrderer.Node([0])
    d = LatticeOrderer.Node([0])
    b = LatticeOrderer.Node([4]).markLessThan(d)
    c = LatticeOrderer.Node([2]).markLessThan(d)
    a = LatticeOrderer.Node([1]).markLessThan(b).markLessThan(c)
    e = LatticeOrderer.Node([5])
    g = LatticeOrderer.Node([3])
    self.orderer.addNodes(a, e, f, g)
    self.compareOrderTo([[0], [1], [2], [3], [4], [0], [5]])

  def testAddEmptyLatticeSequence(self):
    self.orderer.addNodes(LatticeOrderer.Node([0]))
    self.orderer.addOrderedSequence([])

    self.compareOrderTo([[0]])

  def testAddLatticeSequence(self):
    self.orderer.addOrderedSequence(self.generateSequence(range(10, 0, -1)))

    self.compareOrderTo([[i] for i in range(10, 0, -1)])


  def testMakeTupleSequence(self):
    firstElements = self.generateSequence(range(2, 9, 3))
    secondElements = self.generateSequence(range(1, 9, 3))
    thirdElements = self.generateSequence(range(0, 9, 3))
    self.orderer.coupleTuples(firstElements, secondElements, thirdElements)
    self.orderer.addNodes(*firstElements)

    self.compareOrderTo([[2], [1], [0], [5], [4], [3], [8], [7], [6]])

  def testMakeOrderedSequence(self):
    sequence = self.generateSequence(range(5, 0, -1))
    self.orderer.makeOrderedSequence(sequence)
    a = LatticeOrderer.Node([10])
    a.markLessThan(sequence[0])
    self.orderer.addNodes(a)
    self.compareOrderTo([[10], [5], [4], [3], [2], [1]])

  def generateSequence(self, iterator):
    return [LatticeOrderer.Node([i]) for i in iterator]

  def compareOrderTo(self, reference):
    self.assertEqual(self.orderer.pullOrdered(),
                     reference)


if __name__ == '__main__':
  unittest.main()
