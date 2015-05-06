#!/usr/bin/env python
# encoding: utf-8
"""
_Tools.py

Copyright (c) 2012-2015 Laboratory of Neuroinformatics. All rights reserved.
"""
import os
from datetime import datetime, timedelta
import pytz
import time
import warnings
from math import modf

from numbers import Number
import numpy as np
if not issubclass(np.floating, Number):
  Number.register(np.floating)

import heapq


def timeString(x, tz=None):
  return datetime.fromtimestamp(x, tz).strftime('%Y-%m-%d %H:%M:%S.%f%z')


def deprecated(message, warningClass=DeprecationWarning, stacklevel=1):
  warnings.warn(message, warningClass, stacklevel=stacklevel + 2)


def ensureFloat(x):
  """
  Convert x to float if possible.

  Accept ',' used as a decimal mark.

  Convert '' to None.
  """
  if isinstance(x, basestring):
    if x == '':
      return None

    return float(x.replace(',', '.'))

  if x is not None:
    return float(x)


def ensureInt(x):
  """
  Convert x to int if possible.

  Convert '' to None.
  """
  if x == '' or x is None:
    return None

  return int(x)


def hTime(t):
  """
  Convert timestamp t to a human-readible UTC string.
  """
  dec, integer = modf(t)
  return time.strftime("%Y-%m-%d %H:%M:%S" + ('%01.3f' % dec)[1:],
                       time.gmtime(integer))

EPOCH = datetime(1970,1,1)
#UTC_OFFSET = time.mktime(EPOCH.timetuple())

EPOCH_UTC = datetime(1970, 1, 1, tzinfo=pytz.UTC)

def toTimestampUTC(x):
  return (x - EPOCH_UTC).total_seconds()

def toTimestamp(x):
  return (x - EPOCH).total_seconds()



def toDt(tmp):
  if tmp is None or isinstance(tmp, datetime):
    return tmp

  if isinstance(tmp, (tuple, list)):
    return datetime(*tmp)

  if isinstance(tmp, dict):
    return datetime(**tmp)

  tmp = datetime.fromtimestamp(float(tmp))



def convertTime(tStr, tzinfo=None):
  """
  Converts time to timestamp - no timezones assumed.
  """
  tSplit = tStr.replace('-', ' ').replace(':', ' ').split()
  args = map(int, tSplit[:5])
  secs = int(float(tSplit[5]) * 1000000) if len(tSplit) == 6 else 0
  args.extend((secs / 1000000, secs % 1000000, tzinfo))
  return datetime(*args)

def timeToList(tStr):
  date, time = tStr.split()
  tokens = date.split('-') + time.split(':')

  if len(tokens) == 5:
    return map(int, tokens) + [0, 0]

  decimal, seconds = modf(float(tokens[5]))
  return map(int, tokens[:5] + [seconds, round(decimal * 1000000)])

class timeListList(list):
  def __eq__(self, x):
    return self[0] == x[0]

  def __le__(self, x):
    return self[0] <= x[0]

  def __ge__(self, x):
    return self[0] >= x[0]

  def __ne__(self, x):
    return self[0] != x[0]

  def __lt__(self, x):
    return self[0] < x[0]

  def __gt__(self, x):
    return self[0] > x[0]


class timeListQueue(object):
  # soo dirty...
  def __init__(self, lists):
    # list item: [[time list], locked, unlocks]
    tmpLists = filter(None, map(timeListList, lists))
    self.__heap = []
    self.__locked = []
    #self.__seen = set()
    for item in tmpLists:
      if item[0][1]:
        self.__locked.append(item)

      else:
        self.__heap.append(item)

    heapq.heapify(self.__heap)

  def top(self):
    try:
      return self.__heap[0][0][0]

    except IndexError:
      raise StopIteration

  def next(self):
    try:
      head = heapq.heappop(self.__heap)

    except IndexError:
      raise StopIteration

    top, _, unlock = head.pop(0)

    if unlock is not None:
      unlock[1] = False
      for i, locked in list(enumerate(self.__locked)):
        if not locked[0][1]: #found!
          heapq.heappush(self.__heap, locked)
          self.__locked[i:] = self.__locked[i+1:] # -_-
          break

    if head:
      if head[0][1]:
        self.__locked.append(head)

      else:
        heapq.heappush(self.__heap, head)

    return top


  #try:
  #  return time.mktime(time.strptime(tSplit[0], '%Y-%m-%d %H:%M:%S'))\
  #         + subSec

  #except ValueError:
  #  return time.mktime(time.strptime(tSplit[0], '%Y-%m-%d %H:%M'))\
  #         + subSec


class PathZipFile(object):
  """
  A class emulating zipfile.ZipFile behaviour with filesystem directories.
  """
  def __init__(self, path):
    self.__path = path

  def open(self, name, mode='r'):
    fn = os.path.join(self.__path, name)
    return open(fn, mode)
