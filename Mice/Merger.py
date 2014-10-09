#!/usr/bin/env python
# encoding: utf-8
"""
MiceLoader.py

Created by Szymon Łęski on 2012-10-11.

Seriously damaged, then refactored and restored to glory by Jakub Kowalski on
14-15.01.2013.

Copyright (c) 2012-2013 Laboratory of Neuroinformatics. All rights reserved.
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

#from Mice.Data import MiceData, hTime
from .Data import MiceData, hTime

#class HTimeFormatter(matplotlib.ticker.Formatter):
#  

class MiceMerger(MiceData):
  #TODO: common interface, not inheritance
  def __init__(self, *loaders, **kwargs):
    MiceData.__init__(self, verbose = kwargs.get('verbose', False),
                      getNpokes=kwargs.get('get_npokes',
                                           kwargs.get('getNpokes', False)),
                      getEnv=kwargs.get('getEnv', False),
                      getLogs=kwargs.get('getLogs'))

    self._loaders = map(str, loaders)

    self._getHardware = kwargs.get('getHardware', False)

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
    self.icSessionStart = min(x for x in [self.icSessionStart,
                                           loader.getStart()] if x != None)
    self.icSessionEnd = max(x for x in [self.icSessionEnd,
                                         loader.getEnd()] if x != None)

    structure = loader.structure

    # registering animals and groups (if necessary)
    for name in loader.getAnimal():
      animal = loader.getAnimal(name)
      self._registerAnimal(animal)


    for group in loader.getGroup():
      gData = loader.getGroup(group)
      self._registerGroup(**gData)

    visits = loader.getVisits()

    if visits != None:
      if min(v.Start for v in visits) < self.__topTime:
        print "Possible temporal overlap of visits"

      self._insertVisits(visits)

    #TODO:
    #if self._getHardware:
    #  assert 'HardwareEvents' in structure, "HardwareEvents table not found in loader"
    #  hardware = loader.selectAllData('HardwareEvents')
    #  if hardware != None:
    #    if min(hardware['DateTime']) < self.__topTime:
    #      print "Possible temporal overlap of HardwareEvents"

    #    self._insertDataSid(hardware, 'HardwareEvents', sidMapping)

    ##logs goes here
    #assert 'log' in structure, "Log table not found in loader."
    #log = loader.selectAllData('log')
    #if log != None:
    #  if min(log['DateTime']) < self.__topTime:
    #    print "Possible temporal overlap of logs"

    #  self._insertDataSid(log, 'log', sidMapping)

    ## XXX more data loading here

    if visits != None:
      self.__topTime = max(self.__topTime, max(v.End for v in visits))

      if self._getNpokes:
        self.__topTime = max(self.__topTime, max(np.End for v in visits if v.Nosepokes for np in v.Nosepokes))

    # TODO
    #if log != None:
    #  self.__topTime = max(self.__topTime, max(log['DateTime']))

    self._buildCache()

  @staticmethod
  def _newNodes(nodes, cls=None):
    return map(copy.copy, nodes)


if __name__ == '__main__':
  import doctest
  from Mice.Loader import MiceLoader
  testDir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../data/test'))
  ml_a1 = MiceLoader(os.path.join(testDir, 'analyzer_data.txt'))
  ml_l1 = MiceLoader(os.path.join(testDir, 'legacy_data.zip'))
  doctest.testmod(extraglobs={'ml_a1': ml_a1, 'ml_l1': ml_l1})
