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
from matplotlib import rc
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
  from ._Data import Data, hTime

except ValueError:
  try:
    print "from ._Data import... failed"
    from PyMICE._Data import Data, hTime

  except ImportError:
    print "from PyMICE._Data import... failed"
    from _Data import Data, hTime

#class HTimeFormatter(matplotlib.ticker.Formatter):
#  

class Merger(Data):
  """
  >>> mm = Merger(ml_icp3, ml_l1, getNpokes=True)
  >>> for v in mm.getVisits(order='Start'):
  ...   print '%s %d %d' % (str(v.Animal), len(v.Nosepokes), v.Animal.Tag)
  Minnie 0 1337
  Mickey 1 42
  Jerry 2 69
  Minnie 1 1337
  Mickey 1 42
  Jerry 2 69

  >>> mm = Merger(ml_empty, ml_l1, getNpokes=True)
  >>> for v in mm.getVisits(order='Start'):
  ...   print '%s %d' % (str(v.Animal), len(v.Nosepokes))
  Minnie 1
  Mickey 1
  Jerry 2

  >>> mm = Merger(ml_retagged, ml_l1, getNpokes=True)
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
  def __init__(self, *loaders, **kwargs):
    Data.__init__(self,
                  getNpokes=kwargs.get('get_npokes',
                                       kwargs.get('getNpokes',
                                       kwargs.get('getNosepokes',False))),
                  getEnv=kwargs.get('getEnv', False),
                  getLogs=kwargs.get('getLogs', False),
                  getHw=kwargs.get('getHardware', False))

    self._loaders = map(str, loaders)

    self._initCache()
    self.__topTime = float('-inf')

    for loader in loaders:
      try:
        self.appendLoader(loader)

      except:
        print "ERROR processing %s" % loader
        raise

    self._logAnalysis(kwargs.get('loganalyzers', []))

  def __repr__(self):
    """
    @return: Nice string representation for prtinting this class.
    """
    mystring = 'IntelliCage data loaded from: %s' %\
                str(self._loaders)
    return mystring

  def plotData(self):
    #fig, ax = plt.subplots()
    ax = plt.gca()
    ax.xaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda x, y: hTime(x)))
    plt.xticks(rotation=10)
    labels = []
    yticks = []
    times = []
    for i, loader in enumerate(self._loaders):
      labels.append(str(i))
      start = loader.getStart()
      end = loader.getEnd()
      #plt.broken_barh([(start, end - start)], [i - 0.4, 0.8])
      times.extend([start, end])
      loader.plotChannel(i + 0.6, i + 1.4)
      yticks.append(i)

    plt.yticks(yticks, labels)
    start = min(times)
    end = max(times)
    span = end - start
    plt.xlim(start - 0.1 * span, end + 0.1 * span)
    plt.ylim(0, len(self._loaders) + 1)

  def plotChannelR(self, top=1., bottom=0.):
    h = top - bottom
    l = len(self._loaders)
    h2 = h / l
    starts, ends = [], []

    for i, loader in enumerate(self._loaders):
      start, end = loader.plotChannelR(bottom + i * h2, bottom + (i + 1) * h2)
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

  def appendLoader(self, loader):
    if loader.icSessionStart != None:
      if self.icSessionStart != None and self.icSessionEnd != None:
        if self.icSessionStart < loader.icSessionStart\
          and self.icSessionEnd > loader.icSessionStart:
          print 'Overlap of IC sessions detected'

    if loader.icSessionEnd != None:
      if self.icSessionStart != None and self.icSessionEnd != None:
        if self.icSessionStart < loader.icSessionEnd\
          and self.icSessionEnd > loader.icSessionEnd:
          print 'Overlap of IC sessions detected'

    # TODO: overlap issue!
    for attr in ['Start', 'End']:
      icAttr = 'icSession' + attr
      vals = [x for x in [getattr(self, icAttr),
                          getattr(loader, 'get' + attr)()] if x is not None]
      if len(vals) > 0:
        setattr(self, icAttr, min(vals))

    # registering animals and groups (if necessary)
    for name in loader.getAnimal():
      animal = loader.getAnimal(name)
      self._registerAnimal(animal)


    for group in loader.getGroup():
      gData = loader.getGroup(group)
      self._registerGroup(**gData)

    visits = loader.getVisits()

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
      hardware = loader.getHardwareEvents()
      if hardware is not None:
        self._insertHardware(hardware)


    ##logs goes here
    #assert 'log' in structure, "Log table not found in loader."
    #log = loader.selectAllData('log')
    #if log != None:
    #  if min(log['DateTime']) < self.__topTime:
    #    print "Possible temporal overlap of logs"

    #  self._insertDataSid(log, 'log', sidMapping)

    ## XXX more data loading here

    if visits != None:
      maxEnd = [self.__topTime]
      maxEnd.extend(v.End for v in visits)
      if self._getNpokes:
        maxEnd.extend(np.End for v in visits if v.Nosepokes for np in v.Nosepokes)

      self.__topTime = max(maxEnd)

    # TODO
    #if log != None:
    #  self.__topTime = max(self.__topTime, max(log['DateTime']))

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
    from Mice._test import TEST_GLOBALS

  doctest.testmod(extraglobs=TEST_GLOBALS)
