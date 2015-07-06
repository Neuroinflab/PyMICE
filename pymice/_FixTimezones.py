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

from datetime import datetime
from itertools import izip, count, islice

def inferTimezones(timepoints, sessionStart, sessionEnd=None):
  n = len(timepoints)
  if sessionEnd is None or sessionStart.tzinfo == sessionEnd.tzinfo:
    return [sessionStart.tzinfo] * n

  tzDelta = sessionEnd.utcoffset() - sessionStart.utcoffset()

  intervals = getIntervals(sessionEnd, sessionStart, timepoints)
  candidates = [c for (interval, c) in izip(intervals, count(0)) if interval > tzDelta]

  if len(candidates) != 1:
    raise ValueError

  return [sessionStart.tzinfo] * candidates[0] + [sessionEnd.tzinfo] * (n - candidates[0])


def getIntervals(sessionEnd, sessionStart, timepoints):
  dtTimepoints = [sessionStart.replace(tzinfo=None)] + [datetime(*t) for t in timepoints] + [
    sessionEnd.replace(tzinfo=None)]
  intervals = [b - a for (a, b) in izip(dtTimepoints, islice(dtTimepoints, 1, None))]
  return intervals
