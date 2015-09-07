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

import sys
from datetime import datetime, timedelta
try:
  from itertools import izip, islice

except ImportError:
  from itertools import islice
  izip = zip

import numpy as np
import heapq

def inferTimezones(timepoints, sessionStart, sessionEnd=None):
  return TimezonesInferrer(sessionStart, sessionEnd).infer(timepoints)

class TimezonesInferrer(object):
  class AmbigousTimezoneChangeError(ValueError):
    pass

  class TooManyIntervalsBigEnoughForTimeAdvance(AmbigousTimezoneChangeError):
    pass

  class NoIntervalsBigEnoughForTimeAdvance(AmbigousTimezoneChangeError):
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
    return self.getIndexOfTheOnlyTrueElement(self.intervals > self.timeChange,
                                      self.NoIntervalsBigEnoughForTimeAdvance,
                                      self.TooManyIntervalsBigEnoughForTimeAdvance)

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
    minInterval = self.intervals.min()
    if minInterval >= self.zeroTimedelta:
      raise self.AmbigousTimezoneChangeError

    if minInterval < self.timeChange:
      raise self.AmbigousTimezoneChangeError

    return self.getIndexOfTheOnlyTrueElement(self.intervals == minInterval)

  def getIndexOfTheOnlyTrueElement(self, mask,
                                   tooLittle = AmbigousTimezoneChangeError,
                                   tooMany = AmbigousTimezoneChangeError):
    indices = np.where(mask)[0]
    self.ensureOneElementCollection(indices, tooLittle, tooMany)
    return indices[0]

  @staticmethod
  def ensureOneElementCollection(collection, tooLittle, tooMany):
    if len(collection) == 0:
      raise tooLittle

    if len(collection) > 1:
      raise tooMany

  def makeIntervals(self, timepoints):
    dtTimepoints = self.getBoundedTimepoints(timepoints)
    self.intervals = np.array([b - a for (a, b) in
                               izip(dtTimepoints, islice(dtTimepoints, 1, None))])

  def getBoundedTimepoints(self, timepoints):
    return [self.start.replace(tzinfo=None)] +\
           [datetime(*t) for t in timepoints] +\
           [self.end.replace(tzinfo=None)]


class LatticeOrderer(object):
  class Node(list):
    __slots__ = ('__children', '__parents',
                 '_source', '_type', '_line')

    def __init__(self, *args, **kwargs):
      self.__children = []
      self.__parents = 0
      list.__init__(self, *args, **kwargs)

    def markLessThan(self, greaterNode):
      self.__children.append(greaterNode)
      greaterNode.__parents += 1
      return self

    def isMinimal(self):
      return self.__parents == 0

    def getSuccessors(self):
      return self.__children

    def removePredecessor(self):
      self.__parents -= 1


  def __init__(self, elements=[]):
    self.__elements = []

  def pullOrdered(self):
    return list(self)

  def __iter__(self):
    return self

  def next(self):
    try:
      leastElement = heapq.heappop(self.__elements)

    except IndexError:
      raise StopIteration

    else:
      for e in leastElement.getSuccessors():
        e.removePredecessor()
        self.addNodes(e)

      return leastElement

  if sys.version_info >= (3, 0):
    __next__ = next
    del next

  def addNodes(self, *nodes):
    for node in nodes:
      if node.isMinimal():
        heapq.heappush(self.__elements, node)

  def addOrderedSequence(self, sequence):
    self.makeOrderedSequence(sequence)

    if len(sequence) > 0:
      self.addNodes(sequence[0])

  @classmethod
  def coupleTuples(cls, *sequences):
    for sequence in izip(*sequences):
      cls.makeOrderedSequence(sequence)

  @staticmethod
  def makeOrderedSequence(sequence):
    for first, second in izip(sequence, islice(sequence, 1, None)):
      first.markLessThan(second)
