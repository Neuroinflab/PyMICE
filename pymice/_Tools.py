#!/usr/bin/env python
# encoding: utf-8
"""
_Tools.py

Copyright (c) 2012-2015 Laboratory of Neuroinformatics. All rights reserved.
"""
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

class floatDateTime(datetime):
  def __init__(self, *args, **kwargs):
    if len(args) == 1 and isinstance(args[0], datetime):
      tmp = args[0]
      datetime.__init__(self, tmp.year, tmp.month, tmp.day,
                        tmp.hour, tmp.minute, tmp.second,
                        tmp.microsecond, tmp.tzinfo)
      if isinstance(tmp, floatDateTime):
        self.__timestamp = float(tmp)
        return

    else:
      datetime.__init__(self, *args, **kwargs)

    self.__timestamp = datetime.__sub__(self, EPOCH if self.tzinfo is None else EPOCH_UTC).total_seconds()

  def __float__(self):
    return self.__timestamp

  def __int__(self):
    return int(self.__timestamp)

  def __long__(self):
    return long(self.__timestamp)

  def __eq__(self, x):
    if isinstance(x, Number):
      return self.__timestamp == x

    return datetime.__eq__(self, x)

  def __le__(self, x):
    if isinstance(x, Number):
      return self.__timestamp <= x

    return datetime.__le__(self, x)

  def __ge__(self, x):
    if isinstance(x, Number):
      return self.__timestamp >= x

    return datetime.__ge__(self, x)

  def __ne__(self, x):
    if isinstance(x, Number):
      return self.__timestamp != x

    return datetime.__ne__(self, x)

  def __lt__(self, x):
    if isinstance(x, Number):
      return self.__timestamp < x

    return datetime.__lt__(self, x)

  def __gt__(self, x):
    if isinstance(x, Number):
      return self.__timestamp > x

    return datetime.__gt__(self, x)

  def __add__(self, x):
    if isinstance(x, timedelta):
      dt = x.total_seconds()

    elif isinstance(x, (float, int, long)):
      dt = x

    else:
      raise TypeError("unsupported operand type(s) for +: 'floatDateTime' and '%s'" %\
                      x.__class__.__name__)

    tmp = datetime.fromtimestamp(self.__timestamp + dt, self.tzinfo)
    return floatTimeDelta(tmp.year, tmp.month, tmp.day,
                          tmp.hour, tmp.minute, tmp.second,
                          tmp.microsecond, tmp.tzinfo)

  def __radd__(self, x):
    try:
      return self + x

    except TypeError:
       raise TypeError("unsupported operand type(s) for +: '%s' and 'floatDateTime'" %\
                       x.__class__.__name__)

  def __sub__(self, x):
    if isinstance(x, floatDateTime):
      return floatTimeDelta(seconds=self.__timestamp - float(x))

    if isinstance(x, datetime):
      timestamp = (x - (EPOCH if self.tzinfo is None else EPOCH_UTC)).total_seconds()
      return floatTimeDelta(seconds=self.__timestamp - timestamp)

    if isinstance(x, timedelta):
      dt = x.total_seconds()

    elif isinstance(x, (float, int, long)):
      dt = x
      
    else:
      raise TypeError("unsupported operand type(s) for -: 'floatDateTime' and '%s'" %\
                      x.__class__.__name__)

    tmp = datetime.fromtimestamp(self.__timestamp - dt, self.tzinfo)
    return floatDateTime(tmp.year, tmp.month, tmp.day,
                         tmp.hour, tmp.minute, tmp.second,
                         tmp.microsecond, tmp.tzinfo)

  def replace(self, year=None, month=None, day=None, hour=None, minute=None, second=None,
                    microsecond=None, *args, **kwargs):
    tzinfoPresent = ('tzinfo' in kwargs) ^ (len(args) == 1)
    if tzinfoPresent:
      tzinfo = kwargs['tzinfo'] if 'tzinfo' in kwargs else args[0]

    return floatDateTime(self.year if year is None else year,
                         self.month if month is None else month,
                         self.day if day is None else day,
                         self.hour if hour is None else hour,
                         self.minute if minute is None else minute,
                         self.second if second is None else second,
                         self.microsecond if microsecond is None else microsecond,
                         tzinfo if tzinfoPresent else self.tzinfo)

#astimezone
#fromtimestamp
#utcfromtimestamp
#fromordinal
#combine
#strptime
#today
#now
#utcnow


def toFloatDt(tmp):
  if tmp is None or isinstance(tmp, floatDateTime):
    return tmp

  if isinstance(tmp, (tuple, list)):
    return floatDateTime(*tmp)

  if isinstance(tmp, dict):
    return floatDateTime(**tmp)

  if not isinstance(tmp, datetime):
    tmp = datetime.fromtimestamp(float(tmp))

  return floatDateTime(tmp.year, tmp.month, tmp.day,
                       tmp.hour, tmp.minute, tmp.second,
                       tmp.microsecond, tmp.tzinfo)


class floatTimeDelta(timedelta):
  def __float__(self):
    return self.total_seconds()

  def __int__(self):
    return int(self.total_seconds())

  def __long__(self):
    return long(self.total_seconds())

  def __add__(self, x):
    if isinstance(x, timedelta):
      return floatTimeDelta(seconds=self.total_seconds() + x.total_seconds())

    if isinstance(x, (float, int, long)):
      return floatTimeDelta(seconds=self.total_seconds() + x)

    if isinstance(x, floatDateTime):
      timestamp = float(x)

    elif isinstance(x, datetime):
      timestamp = (x - EPOCH if self.tzinfo is None else EPOCH_UTC).total_seconds()
    
    else:
      raise TypeError("unsupported operand type(s) for +: 'floatTimeDelta' and '%s'" %\
                      x.__class__.__name__)

    tmp = datetime.fromtimestamp(self.total_seconds() + timestamp, x.tzinfo)
    return floatDateTime(tmp.year, tmp.month, tmp.day,
                         tmp.hour, tmp.minute, tmp.second,
                         tmp.microsecond, tmp.tzinfo)

  def __radd__(self, x):
    try:
      return self + x

    except TypeError:
      raise TypeError("unsupported operand type(s) for +: '%s' and 'floatTimeDelta'" %\
                      x.__class__.__name__)

  def __sub__(self, x):
    if isinstance(x, timedelta):
      return floatTimeDelta(seconds=self.total_seconds() - x.total_seconds())

    elif isinstance(x, (float, int, long)):
      return floatTimeDelta(seconds=self.total_seconds() - x)

    raise TypeError("unsupported operand type(s) for -: 'floatTimeDelta' and '%s'" %\
                    x.__class__.__name__)

  def __rsub__(self, x):
    if isinstance(x, floatDateTime):
      timestamp = float(x)

    elif isinstance(x, datetime):
      timestamp = (x - (EPOCH if self.tzinfo is None else EPOCH_UTC)).total_seconds()

    else:
      if isinstance(x, timedelta):
        dt = x.total_seconds()

      elif isinstance(x, (float, int, long)):
        dt = x
      
      else:
        raise TypeError("unsupported operand type(s) for -: '%s' and 'floatDateTime'" %\
                        x.__class__.__name__)

      return floatTimeDelta(seconds=dt - self.total_seconds())
        
    tmp = datetime.fromtimestamp(timestamp - self.total_seconds(), x.tzinfo)
    return floatDateTime(tmp.year, tmp.month, tmp.day,
                         tmp.hour, tmp.minute, tmp.second,
                         tmp.microsecond, tmp.tzinfo)

  def __mul__(self, x):
    if isinstance(x, (float, int, long)):
      return floatTimeDelta(seconds=self.total_seconds() * x)

    raise TypeError("unsupported operand type(s) for *: 'floatTimeDelta' and '%s'" %\
                    x.__class__.__name__)

  def __rmul__(self, x):
    try:
      return self * x

    except TypeError:
      raise TypeError("unsupported operand type(s) for *: '%s' and 'floatTimeDelta'" %\
                       x.__class__.__name__)

  def __div__(self, x):
    if isinstance(x, (float, int, long)):
      return floatTimeDelta(seconds=self.total_seconds() / x)

    raise TypeError("unsupported operand type(s) for /: 'floatTimeDelta' and '%s'" %\
                    x.__class__.__name__)

  def __neg__(self):
    return floatTimeDelta(seconds=-self.total_seconds())

  def __abs__(self):
    return floatTimeDelta(seconds=abs(self.total_seconds()))


def convertTime(tStr, tzinfo=None):
  """
  Converts time to timestamp - no timezones assumed.
  """
  tSplit = tStr.replace('-', ' ').replace(':', ' ').split()
  args = map(int, tSplit[:5])
  secs = int(float(tSplit[5]) * 1000000) if len(tSplit) == 6 else 0
  args.extend((secs / 1000000, secs % 1000000, tzinfo))
  return floatDateTime(*args)

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

