#!/usr/bin/env python
# encoding: utf-8
"""
_Merger.py

Copyright (c) 2012-2014 Laboratory of Neuroinformatics. All rights reserved.
"""

import sys
import os
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.path import Path
import matplotlib.ticker
import scipy.interpolate as sip
import time
import zipfile
import csv
import collections
import sqlite3
import codecs
import copy
import warnings
from math import exp, modf
import itertools

try:
  from ._Data import Data
  from ._Tools import hTime, deprecated

except ValueError:
  try:
    print "from .<XXX> import... failed"
    from PyMICE._Data import Data
    from PyMICE._Tools import hTime, deprecated

  except ImportError:
    print "from PyMICE.<XXX> import... failed"
    from _Data import Data
    from _Tools import hTime, deprecated

#class HTimeFormatter(matplotlib.ticker.Formatter):
#  

class Merger(Data):
  """
  >>> mm = Merger(ml_icp3, ml_l1, getNp=True)
  >>> for v in mm.getVisits(order='Start'):
  ...   print '%s %d %d' % (str(v.Animal), len(v.Nosepokes), v.Animal.Tag)
  Minnie 0 1337
  Mickey 1 42
  Jerry 2 69
  Minnie 1 1337
  Mickey 1 42
  Jerry 2 69

  >>> mm = Merger(ml_empty, ml_l1, getNp=True)
  >>> for v in mm.getVisits(order='Start'):
  ...   print '%s %d' % (str(v.Animal), len(v.Nosepokes))
  Minnie 1
  Mickey 1
  Jerry 2

  >>> mm = Merger(ml_retagged, ml_l1, getNp=True)
  >>> for v in mm.getVisits(order='Start'):
  ...   print '%s %d' % (str(v.Animal), len(v.Nosepokes))
  ...   if isinstance(v.Animal.Tag, set):
  ...     print "  %s" % (', '.join(map(str, sorted(v.Animal.Tag))))
  ...   else:
  ...     print "  %d" % v.Animal.Tag
  Mickey 0
    42, 1337
  Minnie 1
    42, 1337
  Jerry 2
    69
  Minnie 1
    42, 1337
  Mickey 1
    42, 1337
  Jerry 2
    69
  """
  #TODO: common interface, not inheritance
  def __init__(self, *dataSources, **kwargs):
    """
    Usage: Merger(data_1, [data_2, ...] [parameters])

    @type data_X: Data

    @param getNp: whether to load nosepoke data (defaults to False).
    @type getNp: bool

    @param getLog: whether to load log (defaults to False).
    @type getLog: bool

    @param getEnv: whether to load environmental data (defaults to False).
    @type getEnv: bool

    @param getHw: whether to load hardware data (defaults to False).
    @type getHw: bool
    """
    getNp = kwargs.pop('getNp', False)
    getLog = kwargs.pop('getLog', False)
    getEnv = kwargs.pop('getEnv', False)
    getHw = kwargs.pop('getHw', False)
    logAnalyzers = kwargs.pop('loganalyzers', [])

    for key, value in kwargs.items():
      if key in ('get_npokes', 'getNpokes', 'getNosepokes'):
        deprecated("Obsolete argument %s given for Merger constructor." % key)
        getNp = value

      elif key == 'getLogs':
        deprecated("Obsolete argument %s given for Merger constructor." % key)
        getLog = value

      elif key == 'getEnvironment':
        deprecated("Obsolete argument %s given for Merger constructor." % key)
        getEnv = value

      elif key in ('getHardware', 'getHardwareEvents'):
        deprecated("Obsolete argument %s given for Merger constructor." % key)
        getHw = value

      else:
        warnings.warn("Unknown argument %s given for Merger constructor" % key, stacklevel=2)

    Data.__init__(self, getNp=getNp, getLog=getLog, getEnv=getEnv, getHw=getHw)

    self._dataSources = map(str, dataSources)

    self._initCache()
    self.__topTime = float('-inf')

    for dataSource in dataSources:
      try:
        self.appendDataSource(dataSource)

      except:
        print "ERROR processing %s" % dataSource
        raise

    self._logAnalysis(logAnalyzers)

  def __repr__(self):
    """
    @return: Nice string representation for prtinting this class.
    """
    mystring = 'IntelliCage data loaded from: %s' %\
                str(self._dataSources)
    return mystring

  def plotData(self):
    #fig, ax = plt.subplots()
    ax = plt.gca()
    ax.xaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda x, y: hTime(x)))
    plt.xticks(rotation=10)
    labels = []
    yticks = []
    times = []
    for i, dataSource in enumerate(self._dataSources):
      labels.append(str(i))
      start = dataSource.getStart()
      end = dataSource.getEnd()
      #plt.broken_barh([(start, end - start)], [i - 0.4, 0.8])
      times.extend([start, end])
      dataSource.plotChannel(i + 0.6, i + 1.4)
      yticks.append(i)

    plt.yticks(yticks, labels)
    start = min(times)
    end = max(times)
    span = end - start
    plt.xlim(start - 0.1 * span, end + 0.1 * span)
    plt.ylim(0, len(self._dataSources) + 1)

  def plotChannelR(self, top=1., bottom=0.):
    h = top - bottom
    l = len(self._dataSources)
    h2 = h / l
    starts, ends = [], []

    for i, dataSource in enumerate(self._dataSources):
      start, end = dataSource.plotChannelR(bottom + i * h2, bottom + (i + 1) * h2)
      starts.append(start)
      ends.append(end)

    if self.maskTimeStart is not None and self.maskTimeEnd is not None:
      left = self.maskTimeStart if self.maskTimeStart is not None else self.getStart()
      right = self.maskTimeEnd if self.maskTimeEnd is not None else self.getEnd()
      ax = plt.gca()
      codes = [Path.MOVETO, Path.LINETO]
      verts = [(left, top), (right, top)]
      if self.maskTimeEnd is not None:
        codes.append(Path.LINETO)
        ends.append(self.maskTimeEnd)

      else:
        codes.append(Path.MOVETO)

      verts.append((right, bottom))
      codes.append(Path.LINETO)
      verts.append((left, bottom))
      if self.maskTimeStart is not None:
        verts.append((left, top))
        codes.append(Path.CLOSEPOLY)
        starts.append(self.maskTimeStart)

      path = Path(verts, codes)
      patch = patches.PathPatch(path, facecolor='none', edgecolor='red')
      ax.add_patch(patch)
      

    return min(starts), max(ends)

  def appendDataSource(self, dataSource):
    if dataSource.icSessionStart != None:
      if self.icSessionStart != None and self.icSessionEnd != None:
        if self.icSessionStart < dataSource.icSessionStart\
          and self.icSessionEnd > dataSource.icSessionStart:
          print 'Overlap of IC sessions detected'

    if dataSource.icSessionEnd != None:
      if self.icSessionStart != None and self.icSessionEnd != None:
        if self.icSessionStart < dataSource.icSessionEnd\
          and self.icSessionEnd > dataSource.icSessionEnd:
          print 'Overlap of IC sessions detected'

    # TODO: overlap issue!
    for attr in ['Start', 'End']:
      icAttr = 'icSession' + attr
      vals = [x for x in [getattr(self, icAttr),
                          getattr(dataSource, 'get' + attr)()] if x is not None]
      if len(vals) > 0:
        setattr(self, icAttr, min(vals))

    # registering animals and groups (if necessary)
    for name in dataSource.getAnimal():
      animal = dataSource.getAnimal(name)
      self._registerAnimal(animal)


    for group in dataSource.getGroup():
      gData = dataSource.getGroup(group)
      self._registerGroup(**gData)

    visits = dataSource.getVisits()

    if visits != None:
      try:
        minStart = min(v.Start for v in visits)

      except ValueError:
        pass

      else:
        if minStart < self.__topTime:
          print "Possible temporal overlap of visits"

      self._insertVisits(visits)

    if self._getHw:
      hardware = dataSource.getHardwareEvents()
      if hardware is not None:
        self._insertHardware(hardware)

    if self._getLog:
      log = dataSource.getLog()
      if log is not None:
        self._insertLog(log)

    ## XXX more data loading here

    if visits != None:
      maxEnd = [self.__topTime]
      maxEnd.extend(v.End for v in visits)
      if self._getNp:
        maxEnd.extend(np.End for v in visits if v.Nosepokes for np in v.Nosepokes)

      self.__topTime = max(maxEnd)

    if self._getHw and hardware:
      self.__topTime = max(self.__topTime, max(hw.DateTime for hw in hardware))

    if self._getLog and log:
      self.__topTime = max(self.__topTime, max(l.DateTime for l in log))

    self._buildCache()

  @staticmethod
  def _newNodes(nodes, cls=None):
    return map(copy.copy, nodes)


if __name__ == '__main__':
  import doctest
  try:
    from _test import TEST_GLOBALS

  except ImportError:
    print "from _test import... failed"
    from PyMICE._test import TEST_GLOBALS

  doctest.testmod(extraglobs=TEST_GLOBALS)
