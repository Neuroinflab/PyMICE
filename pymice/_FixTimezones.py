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

from datetime import datetime, timedelta
from itertools import izip, count, islice
import numpy as np

def inferTimezones(timepoints, sessionStart, sessionEnd=None):
  return TimezonesInferrer(sessionStart, sessionEnd).infer(timepoints)


class TimezonesInferrer(object):
  class AmbigousTimezoneChangeError(ValueError):
    pass

  zeroTimedelta = timedelta(0)

  def __init__(self, sessionStart, sessionEnd):
    self.start = sessionStart
    self.end = sessionEnd

  def isTimeAdvanced(self):
    return self.timeChange > self.zeroTimedelta

  def isTimePreserved(self):
    return self.end is None or self.start.tzinfo == self.end.tzinfo

  def inferWhenTimeAdvances(self):
    return self.prepareTimezoneList(self.findFirstAdvancedTimePoint())

  def prepareTimezoneList(self, firstChanged):
    return [self.start.tzinfo] * firstChanged + [self.end.tzinfo] * (
    self.timepointsNumber - firstChanged)

  def findFirstAdvancedTimePoint(self):
    candidates = [c for (interval, c) in izip(self.intervals, count(0)) if
                  interval > self.timeChange]
    if len(candidates) != 1:
      raise self.AmbigousTimezoneChangeError

    return candidates[0]

  def infer(self, timepoints):
    self.timepointsNumber = len(timepoints)
    if self.isTimePreserved():
      return [self.start.tzinfo] * self.timepointsNumber

    self.timeChange = self.end.utcoffset() - self.start.utcoffset()
    self.makeIntervals(timepoints)
    if self.isTimeAdvanced():
      return self.inferWhenTimeAdvances()

    return self.inferWhenTimeBacks()

  def inferWhenTimeBacks(self):
    return self.prepareTimezoneList(self.findFirstBackedTimePoint())

  def findFirstBackedTimePoint(self):
    candidate = np.argmin(self.intervals)
    if self.intervals[candidate] >= self.zeroTimedelta:
      raise self.AmbigousTimezoneChangeError

    if self.intervals[candidate] < self.timeChange:
      raise self.AmbigousTimezoneChangeError

    return candidate

  def makeIntervals(self, timepoints):
    dtTimepoints = self.getBoundedTimepoints(timepoints)
    self.intervals = [b - a for (a, b) in
                      izip(dtTimepoints, islice(dtTimepoints, 1, None))]

  def getBoundedTimepoints(self, timepoints):
    return [self.start.replace(tzinfo=None)] +\
           [datetime(*t) for t in timepoints] +\
           [self.end.replace(tzinfo=None)]
