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
import os
from datetime import datetime
import time
import warnings
from math import modf
from operator import attrgetter

import pytz

try:
  from itertools import imap

except ImportError:
  imap = map

from numbers import Number
import numpy as np
if not issubclass(np.floating, Number):
  Number.register(np.floating)

from ._FixTimezones import LatticeOrderer

if sys.version_info >= (3, 0):
  basestring = str

def timeString(x, tz=None):
  return datetime.fromtimestamp(x, tz).strftime('%Y-%m-%d %H:%M:%S.%f%z')


class PmWarnings(object):
  class PmWarning(Warning):
    """
    A virtual class of PyMICE warnings always to be reported
    - a hook for U{4180-wontfix-issue <http://bugs.python.org/issue4180>}
    """
    pass
  
  class PmDeprecationWarning(DeprecationWarning, PmWarning):
    pass
  
  class PmUserWarning(UserWarning, PmWarning):
    pass

  __initialized__ = False

  def __init__(self):
    if not PmWarnings.__initialized__:
      warnings.filterwarnings('always',
                              category=PmWarnings.PmWarning)
      PmWarnings.__initialized__ = True

    self.enable()

  def disable(self):
    self.enabled = False

  def enable(self):
    self.enabled = True

  def deprecated(self, message, stacklevel=1):
    warnings.warn(message,
                  self.PmDeprecationWarning if self.enabled else DeprecationWarning,
                  stacklevel=stacklevel + 2)

  def warn(self, message, stacklevel=1):
    warnings.warn(message,
                  self.PmUserWarning if self.enabled else UserWarning,
                  stacklevel=stacklevel + 2)


warn = PmWarnings()

# def ensureFloat(x):
#   """
#   Convert x to float if possible.
#
#   Accept ',' used as a decimal mark.
#
#   Convert '' to None.
#   """
#   if isinstance(x, basestring):
#     if x == '':
#       return None
#
#     return float(x.replace(',', '.'))
#
#   if x is not None:
#     return float(x)
#
#
# def ensureInt(x):
#   """
#   Convert x to int if possible.
#
#   Convert '' to None.
#   """
#   if x == '' or x is None:
#     return None
#
#   return int(x)


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

  >>> convertTime('1970-01-01 12:34:56.7')
  datetime.datetime(1970, 1, 1, 12, 34, 56, 700000)
  """
  tSplit = tStr.replace('-', ' ').replace(':', ' ').split()
  args = list(imap(int, tSplit[:5]))
  secs = int(float(tSplit[5]) * 1000000) if len(tSplit) == 6 else 0
  args.extend((secs // 1000000, secs % 1000000, tzinfo))
  return datetime(*args)

def timeToList(tStr):
  date, time = tStr.split()
  tokens = date.split('-') + time.split(':')

  if len(tokens) == 5:
    return map(int, tokens) + [0, 0]

  decimal, seconds = modf(float(tokens[5]))
  #return map(int, tokens[:5] + [seconds, round(decimal * 1000000)])
  return LatticeOrderer.Node(map(int, tokens[:5] + [seconds, round(decimal * 1000000)]))

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


class PathZipFile(object):
  """
  A class emulating zipfile.ZipFile behaviour with filesystem directories.
  """
  def __init__(self, path):
    self.__path = path

  def open(self, name, mode='r'):
    fn = os.path.join(self.__path, name)
    return open(fn, mode)


def getTutorialData(path=None):
  """
  Download example dataset(s) used in tutorials.

  @param path: a directory where tutorial data are to be loaded into
               (defaults to working directory)
  @type path: basestring
  """

  #fraction = [0]
  def reporthook(blockcount, blocksize, totalsize):
    downloaded = blockcount * blocksize * 100 // totalsize
    if downloaded > fraction[0]:
      print("%3d%% downloaded." % downloaded)
      fraction[0] += 25


  if path is None:
    path = os.getcwd()

  if not os.path.exists(path):
    os.makedirs(path)

  elif not os.path.isdir(path):
    raise OSError("Not a directory: '%s'" % path)

  DATA = {'https://www.dropbox.com/s/0o5faojp14llalm/C57_AB.zip?dl=1':
           {'C57_AB/2012-08-28 13.44.51.zip': 86480,
            'C57_AB/2012-08-31 11.58.22.zip': 3818445,
            'C57_AB/2012-08-28 15.33.58.zip': 494921,
            'C57_AB/2012-08-31 11.46.31.zip': 29344,
            'C57_AB/timeline.ini': 2894,
           },
         }

  toDownload = {}
  for url, files in DATA.items():
    if all(os.path.isfile(os.path.join(path, fn)) and \
           os.path.getsize(os.path.join(path, fn)) == fs \
           for (fn, fs) in files.items()):
      print("%s data already downloaded." % url)
      continue

    toDownload[url] = sorted(files.items())

  if not toDownload:
    print("All data already downloaded.")
    print("")
    return

  print("In case the automatic download fails fetch the data manually.")
  for url, files in toDownload.items():

    print("Download archive from: %s" % url)
    print("then extract the following files:")
    for filename, _ in files:
      print("- %s" % filename)
  
    print("")
  
  print("")

  import tempfile
  import zipfile
  try:
   from urllib import urlretrieve

  except ImportError:
    from urllib.request import urlretrieve

  for url, files in toDownload.items():
    print("downloading data from %s" % url)
    fh, fn = tempfile.mkstemp(suffix=".zip", prefix="PyMICE_download_tmp_")
    os.close(fh)
    try:
      fraction = [0]
      urlretrieve(url, fn, reporthook)
      print('data downloaded')
      zf = zipfile.ZipFile(fn)
      for filename, filesize in files:
        print("extracting file %s" % filename)
        zf.extract(filename, path)
        if os.path.getsize(os.path.join(path, filename)) != filesize:
          print('Warning: size of extracted file differs')

      zf.close()

    finally:
      os.remove(fn)


def groupBy(objects, getKey):
  """
  >>> import operator
  >>> output = groupBy([(1, 2), (3, 4), (3, 2), (1, 1), (2, 1, 8)],
  ...                  getKey=operator.itemgetter(1))
  >>> for k in sorted(output):
  ...   print("%s %s" % (k, output[k]))
  1 [(1, 1), (2, 1, 8)]
  2 [(1, 2), (3, 2)]
  4 [(3, 4)]

  >>> output = groupBy([(1, 2), (2, 1), (0, 2), (3, 0), (1, 1), (1, 1)],
  ...                  getKey=lambda x: x[0] + x[1])
  >>> for k in sorted(output):
  ...   print("%s %s" % (k, output[k]))
  2 [(0, 2), (1, 1), (1, 1)]
  3 [(1, 2), (2, 1), (3, 0)]

  >>> groupBy([], getKey=lambda x: x[0] + x[1])
  {}

  >>> output = groupBy([Pair(1, 2), Pair(1, 1), Pair(2, 1)], 'a')
  >>> for k in sorted(output):
  ...   print("%s %s" % (k, output[k]))
  1 [Pair(a=1, b=2), Pair(a=1, b=1)]
  2 [Pair(a=2, b=1)]

  >>> output = groupBy([Pair(1, 2), Pair(1, 1), Pair(2, 1)], ('a', 'b'))
  >>> for k in sorted(output):
  ...   print("%s %s" % (k, output[k]))
  (1, 1) [Pair(a=1, b=1)]
  (1, 2) [Pair(a=1, b=2)]
  (2, 1) [Pair(a=2, b=1)]
  """
  if not hasattr(getKey, '__call__'):
    getKey = attrgetter(getKey) if isinstance(getKey, basestring) else attrgetter(*getKey)

  result = {}
  for o in objects:
    key = getKey(o)
    try:
      result[key].append(o)

    except KeyError:
      result[key] = [o]

  return result

def mergeIntervalsValues(objects, getData, overlap=False, mergeWindow=None):
  if len(objects) == 0:
    return []

  if not hasattr(getData, '__call__'):
    getData = attrgetter(*getData)

  result = []
  data = sorted(map(getData, objects))
  row = data[0]
  lastStart, lastEnd = row[:2]
  assert lastStart <= lastEnd

  lastValue = row[2:]

  for row in data[1:]:
    start, end = row[:2]
    value = row[2:]
    assert overlap or lastEnd <= start
    assert start <= end
    if lastValue == value and (start - lastEnd <= mergeWindow or mergeWindow is None):
      lastEnd = max(end, lastEnd)

    else:
      result.append((lastStart, lastEnd, lastValue))
      lastStart, lastEnd, lastValue = start, end, value

  result.append((lastStart, lastEnd, lastValue))
  return result
