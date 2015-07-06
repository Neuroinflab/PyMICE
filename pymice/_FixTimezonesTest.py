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

from _FixTimezones import inferTimezones


utc = pytz.utc
utcDST = pytz.timezone('Etc/GMT-1')

sessionStart = datetime(2015, 7, 4, 17, 40, tzinfo=utc)
sessionEnd = datetime(2015, 7, 4, 20, 40, tzinfo=utc)
timeChange = datetime(2015, 7, 4, 18, 40, tzinfo=utc)
minute = timedelta(seconds=60)

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

  @unittest.skip("refactoring in progress")
  def testDetectionChangeToDST(self):
    timepointsUTC, timezonesUTC = makeTestCases(sessionStart, timeChange, minute)
    timepointsDST, timezonesDST = makeTestCases(timeChange.astimezone(utcDST),
                                       sessionEnd.astimezone(utcDST),
                                       minute)
    inferred = inferTimezones(timepointsUTC + timepointsDST, sessionStart, sessionEnd.astimezone(utcDST))
    self.assertEqual(inferred, timezonesUTC + timezonesDST)


if __name__ == '__main__':
  unittest.main()
