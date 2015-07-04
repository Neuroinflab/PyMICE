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

from datetime import datetime
import pytz

from _FixTimezones import fixTimezones

sessionStart = datetime(2015, 7, 4, 17, 40, tzinfo=pytz.utc)
sessionEnd = datetime(2015, 7, 4, 18, 40, tzinfo=pytz.utc)


class TestFixTimezones(unittest.TestCase):
  def testEmptyTimepointsStayEmpty(self):
    timepoints = []
    fixTimezones(timepoints, sessionStart)
    self.assertEqual(timepoints, [])

    fixTimezones(timepoints, sessionStart, sessionEnd)
    self.assertEqual(timepoints, [])

  def testInSessionTimepointsGetSameTimezoneAsBothStartAndEnd(self):
    timepoints = [[2015, 7, 4, 17, 45, 15, 0]]
    fixTimezones(timepoints, sessionStart, sessionEnd)
    self.assertEqual(timepoints, [[2015, 7, 4, 17, 45, 15, 0, pytz.utc]])

    timepoints = [[2015, 7, 4, 17, 45, 15, 0],
                  [2015, 7, 4, 17, 56, 43, 1]]
    fixTimezones(timepoints, sessionStart, sessionEnd)
    self.assertEqual(timepoints, [[2015, 7, 4, 17, 45, 15, 0, pytz.utc],
                                  [2015, 7, 4, 17, 56, 43, 1, pytz.utc]])

  def testInOpenSessionTimepointsGetSameTimezoneAsStart(self):
    timepoints = [[2015, 7, 4, 17, 45, 15, 0]]
    fixTimezones(timepoints, sessionStart, None)
    self.assertEqual(timepoints, [[2015, 7, 4, 17, 45, 15, 0, pytz.utc]])

    timepoints = [[2015, 7, 4, 17, 45, 15, 0],
                  [2015, 7, 4, 17, 56, 43, 1]]
    fixTimezones(timepoints, sessionStart, None)
    self.assertEqual(timepoints, [[2015, 7, 4, 17, 45, 15, 0, pytz.utc],
                                  [2015, 7, 4, 17, 56, 43, 1, pytz.utc]])
    

if __name__ == '__main__':
  unittest.main()
