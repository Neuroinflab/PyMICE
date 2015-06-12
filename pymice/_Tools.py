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
      unlock[1] -= 1
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


def getTutorialData(path=None):
  """
  Download example dataset(s) used in tutorials.

  @param path: a directory where tutorial data are to be loaded into
               (defaults to working directory)
  @type path: basestring
  """

  #fraction = [0]
  def reporthook(blockcount, blocksize, totalsize):
    downloaded = blockcount * blocksize * 100 / totalsize
    if downloaded > fraction[0]:
      print "%3d%% downloaded." % downloaded
      fraction[0] += 25


  if path is None:
    path = os.getcwd()

  if not os.path.exists(path):
    os.makedirs(path)

  elif not os.path.isdir(path):
    raise OSError("Not a directory: '%s'" % path)

  DATA = {'https://www.dropbox.com/s/kxgfu7fazbwvz7e/C57_AB.zip?dl=1':
           {'C57_AB/2012-08-28 13.44.51.zip': 86480,
            'C57_AB/2012-08-31 11.58.22.zip': 3818445,
            'C57_AB/2012-08-28 15.33.58.zip': 494921,
            'C57_AB/2012-08-31 11.46.31.zip': 29344,
           },
         }

  toDownload = {}
  for url, files in DATA.items():
    if all(os.path.isfile(os.path.join(path, fn)) and \
           os.path.getsize(os.path.join(path, fn)) == fs \
           for (fn, fs) in files.items()):
      print "%s data already downloaded." % url
      continue

    toDownload[url] = sorted(files.items())

  if not toDownload:
    print "All data already downloaded."
    print
    return

  print "In case the automatic download fails fetch the data manually."
  for url, files in toDownload.items():

    print "Download archive from: %s" % url
    print "then extract the following files:"
    for filename, _ in files:
      print "- %s" % filename
  
    print
  
  print

  import tempfile
  import zipfile
  import urllib

  for url, files in toDownload.items():
    print "downloading data from %s" % url
    fh, fn = tempfile.mkstemp(suffix=".zip", prefix="PyMICE_download_tmp_")
    os.close(fh)
    try:
      fraction = [0]
      urllib.urlretrieve(url, fn, reporthook)
      print 'data downloaded'
      zf = zipfile.ZipFile(fn)
      for filename, filesize in files:
        print "extracting file %s" % filename
        zf.extract(filename, path)
        if os.path.getsize(os.path.join(path, filename)) != filesize:
          print 'Warning: size of extracted file differs'

      zf.close()

    finally:
      os.remove(fn)
