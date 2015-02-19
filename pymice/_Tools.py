#!/usr/bin/env python
# encoding: utf-8
"""
_Tools.py

Copyright (c) 2012-2015 Laboratory of Neuroinformatics. All rights reserved.
"""
from datetime import datetime
import time
import warnings
from math import modf
import collections

import numpy as np
#import matplotlib.dates as mpd
#import matplotlib.pyplot as plt
import matplotlib.mlab as mmlab


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

class ExcludeMouseData(object):
  """
  A class for storing information about excluded data segments / modalities
  """
  def __init__(self, startTime=0., endTime=0., logType=None, notes=None, **kwargs):
    self.startTime = startTime
    self.endTime = endTime
    self.logType = logType
    # logtype should be one of: Lickometer, Presence, Corner, Cage, SocialBox, 
    # AnimalGate, ???
    self.notes = notes
    
    # The rest of the fields goes to the location dictionary
    self.location = {}
    for key in ['cage', 'corner', 'side']:
      self.location[key] = kwargs.pop(key, None)

    self.location.extend(kwargs)
          
  def __repr__(self):
    ss = '\n'.join(['Exclude %s from %s to %s' %(self.logType, 
                    time.strftime('%d.%m %H:%M', 
                            time.localtime(self.startTime)), 
                    time.strftime('%d.%m %H:%M', 
                            time.localtime(self.endTime))),
                   'in location: %s.' %(', '.join([key + ' = ' + str(value)
                   for key, value in self.location.iteritems()]))])
    if self.notes is not None:
      ss = '\n'.join([ss, '', 'Notes:', self.notes])

    return ss


class ILogAnalyzer(object):
  def __call__(self, md):  
    raise NotImplementedError("Virtual method called")

class LickometerLogAnalyzer(ILogAnalyzer):
  def __init__(self, shortThreshold=3, medThreshold=None):
    self.shortThreshold = shortThreshold
    self.medThreshold = 4 * shortThreshold if medThreshold is None else medThreshold

    self.medBin = 3600. # 1-hour bins for final processing
    self.shortBin = 900.
    self.notes = '\n'.join(['Generated by LickometerLogAnalyzer with ',
                          'shortThreshold = %3.2f, medThreshold = %3.2f' 
                          %(self.shortThreshold, self.medThreshold), '', ''])
  
  def __call__(self, md):
    # TODO Make sure we do not get strange starting and ending times
    # resulting from strange bins
    results = []
    log = md.getLog()
    for cage in md.getInmates():
      for side in range(1, 9):
        tt = np.array([float(l.DateTime) for l in log \
                       if l.Type == 'Lickometer' and l.Cage == cage and l.Side == side])
        if len(tt) > 0:
          ttMin = tt.min()
          span = tt.max() - ttMin
          nBins = np.ceil(span / self.medBin)
          medBins = np.linspace(ttMin, ttMin + nBins * self.medBin, int(nBins) + 1)
          medHist, _ = np.histogram(tt, bins=medBins)
          # short_bins = np.arange(tt.min(), tt.max() 
          #              + self.short_bin, self.short_bin)
          # short_hist = np.histogram(tt, bins=short_bins)[0]
          if (medHist > self.medThreshold).any(): 
            # or np.all(short_hist > self.threshold_short):
            pass
            idcs = mmlab.contiguous_regions(medHist > self.medThreshold)
            # print idcs
            for tstartidx, tstopidx in idcs:
              tstart = medBins[tstartidx]
              tstop = medBins[tstopidx]
              # print tstart, tstop
              results.append(ExcludeMouseData(startTime=tstart,
                      endTime=tstop, logType='Lickometer',
                      cage=cage, side=side,
                      notes=str(sum(med_hist[tstartidx:tstopidx])) 
                      + ' cases. ' + self.notes))

    return results 

class OldLogAnalyzer(ILogAnalyzer):
  """Moved here from miceloader2, just prints warnings and errors"""
  def __call__(self, md):
    log = md.getLog()
    errors = [l for l in log if l.Category  == 'Error' and l.Type not in ('Lickometer', 'Nosepoke')]

    if len(errors) > 0:
      print '%d errors' % len(errors)

    warnings = [l for l in log if l.Notes.startswith('Unregistered tag') or l.Notes.startswith('Presence signal')]

    if len(warnings) > 0:
      print '%d warnings in logs' % len(warnings) 
      notes = collections.Counter(l.Notes for l in warnings)
      for note, n in sorted(notes.items()):
        print "%s: %d time(s)" % (note, n)
      

class PresenceLogAnalyzer(ILogAnalyzer):
  """Analyze 'presence' errors"""
  def __init__(self):
    self.notes = '\n'.join(['Generated by PresenceLogAnalyzer', '', ''])
    self.finBin = 3600. # Final bins: 1 hour
  
  def __call__(self, md):
    results = []
    log = md.getLog(order='DateTime')
    for cage in md.getInmates():
      for corner in range(1, 5):
        tt = np.array([float(l.DateTime) for l in log \
                       if l.Cage == cage and l.Corner == corner and l.Notes.startswith('Presence signal')])
        if len(tt) > 0:
          # print cage, corner, len(events)
          ttOrig = tt.copy()
          tds = np.diff(tt)  
    
          # # Wywalanie jesli sa co najmniej 3 w czasie ponizej minuty
          # idcs = np.zeros_like(tt)
          # for idx, there, dthere in zip(range(len(tt)-1), tt[:-1], tds):
          #     if dthere < 60.:
          #         # print idx, there, dthere
          #         idx2 = np.where((tt >= there)&(tt < there + 60.))[0]
          #         # print idx, idx2
          #         if len(idx2) >= 3:
          #             idcs[idx2] = 1 
          # print idcs
          # tt = np.delete(tt, np.where(idcs))
      
          # Wywalamy blizsze siebie niz 30 s
          idcs = np.zeros_like(tt)
          idcs[tds < 30.] = 1
          tds = np.r_[np.nan, tds]
          idcs[tds < 30.] = 1
          tt = np.delete(tt, np.where(idcs))
          
          if len(tt) > 0:  
            # Wywalamy jesli izolowany
            tds = np.diff(tt)
            idcs = np.zeros_like(tt) 
            idcs[0] += 0.5
            idcs[-1] += 0.5
            idcs[tds > 1800.] += 0.5
            tds = np.r_[np.nan, tds] 
            idcs[tds > 1800.] += 0.5          
            tt = np.delete(tt, np.where(idcs > 0.75))

          if len(tt) > 0:
            # Pomijamy jesli <= 4 bledy w dobie
            ttMin = tt.min()
            span = tt.max() - ttMin
            nBins = np.ceil(span / (24 * 3600.))
            longBins = np.linspace(ttMin, ttMin + nBins * 24 * 3600.,
                                   int(nBins) + 1)
            hist, _ = np.histogram(tt, bins=longBins)
            if np.all(hist > 4).any():
              # print cage, corner, 'Zostalo ', len(tt)
              nBins = np.ceil(span / self.finBin)
              bins = np.arange(ttMin, ttMin + nBins * self.finBin,
                               int(nBins) + 1)
              hist, _ = np.histogram(tt, bins=bins)
              idcs = mmlab.contiguous_regions(hist)
              for tstartidx, tstopidx in idcs:
                tstart = bins[tstartidx]
                tstop = bins[tstopidx]
                results.append(ExcludeMouseData(startTime=tstart,
                        endTime=tstop, logType='Presence',
                        cage=cage, corner=corner, 
                        notes=str(sum(hist[tstartidx:tstopidx])) 
                        + ' cases. ' + self.notes))

    return results                    
