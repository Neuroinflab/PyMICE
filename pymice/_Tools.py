#!/usr/bin/env python
# encoding: utf-8
"""
_Data.py

Copyright (c) 2012-2014 Laboratory of Neuroinformatics. All rights reserved.
"""

from datetime import datetime
import time
import warnings
from math import modf


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
  Convert timestamp t to a human-readible string.
  """
  dec, integer = modf(t)
  return time.strftime("%Y-%m-%d %H:%M:%S" + ('%01.3f' % dec)[1:],
                       time.localtime(integer))

EPOCH = datetime(1970,1,1)
UTC_OFFSET = time.mktime(EPOCH.timetuple())

def convertTime(tStr):
  tSplit = tStr.replace('-', ' ').replace(':', ' ').split()
  subSec = float(tSplit[5]) if len(tSplit) == 6 else 0.
  return (datetime(*map(int, tSplit[:5])) - EPOCH).total_seconds() + subSec + UTC_OFFSET # a hook for backward compatibility

  #try:
  #  return time.mktime(time.strptime(tSplit[0], '%Y-%m-%d %H:%M:%S'))\
  #         + subSec

  #except ValueError:
  #  return time.mktime(time.strptime(tSplit[0], '%Y-%m-%d %H:%M'))\
  #         + subSec
