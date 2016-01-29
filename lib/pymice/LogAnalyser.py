#!/usr/bin/env python
# encoding: utf-8
###############################################################################
#                                                                             #
#    PyMICE library                                                           #
#                                                                             #
#    Copyright (C) 2013-2016 Jakub M. Kowalski, S. Łęski (Laboratory of       #
#    Neuroinformatics; Nencki Institute of Experimental Biology of Polish     #
#    Academy of Sciences)                                                     #
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

from datetime import datetime
from pytz import UTC
from math import ceil
import collections

import numpy as np
import matplotlib.mlab as mmlab

from ._Tools import toTimestampUTC


class DataValidator(object):
  """
  A class of objects performing data validation.
  """
  def __init__(self, *analyzers):
    """
    :arg analyzers: a set of analyzers defining validation criteria
    """
    self.__analyzers = tuple(analyzers)

  def __call__(self, data):
    """
    :param data: data to be validated
    :type data: :py:class:`pymice.Data.Data`

    :return: description of data found invalid
    :rtype: (:py:class:`ExcludeMiceData`, ...)
    """
    excluded = []
    for analyzer in self.__analyzers:
      excluded.extend(analyzer(data))

    return tuple(excluded)


class ExcludeMiceData(object):
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

    self.location.update(kwargs)

  def __repr__(self):
    ss = 'Exclude %s from %s to %s\nin location: %s.'\
          % (self.logType,
             self.startTime.strftime("%Y-%m-%d %H:%M:%S.%f"),
             self.endTime.strftime("%Y-%m-%d %H:%M:%S.%f"),
             ', '.join('%s = %s' % x for x in self.location.items()),)
    if self.notes is not None:
      ss += '\n\nNotes:\n' + self.notes

    return ss



class LickometerLogAnalyzer(object):
  """
  A class of objects detecting Lickometer type of warnings.

  'Lickometer is active but nosepoke is inactive' errors might indicate
  a failure of the lickometer.
  """
  def __init__(self, shortThreshold=3, medThreshold=None):
    """
    :param shortThreshold: not used explicitly
    :type shortThreshold: int or float

    :param medThreshold: a maximal acceptable number of lickometer warnings
                         within 1 hour bin; defaults to 4*``shortThreshold``
    :type medThreshold: int or float
    """
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
        # XXX: idea - get timestamps from md._Data_logDateTime
        tt = np.array([toTimestampUTC(l.DateTime) for l in log \
                       if l.Type == 'Lickometer' and l.Cage == cage and l.Side == side])
        if len(tt) > 0:
          ttMin = tt.min()
          span = tt.max() - ttMin
          nBins = ceil(span / self.medBin)
          medBins = np.linspace(ttMin, ttMin + nBins * self.medBin, int(nBins) + 1)
          medHist, _ = np.histogram(tt, bins=medBins)
          # short_bins = np.arange(tt.min(), tt.max()
          #              + self.short_bin, self.short_bin)
          # short_hist = np.histogram(tt, bins=short_bins)[0]
          if (medHist > self.medThreshold).any():
            # or np.all(short_hist > self.threshold_short):
            pass
            idcs = mmlab.contiguous_regions(medHist > self.medThreshold)
            # print(idcs)
            for tstartidx, tstopidx in idcs:
              tstart = medBins[tstartidx]
              tstop = medBins[tstopidx]
              # print('%s\t%s" % (tstart, tstop))
              results.append(ExcludeMiceData(startTime=datetime.fromtimestamp(tstart, UTC),
                      endTime=datetime.fromtimestamp(tstop, UTC), logType='Lickometer',
                      cage=cage, side=side,
                      notes=str(sum(medHist[tstartidx:tstopidx]))
                      + ' cases. ' + self.notes))

    return tuple(results)


class OldLogAnalyzer(object):
  """
  Class which objects just print warnings and errors.
  """
  def __call__(self, md):
    log = md.getLog()
    errors = [l for l in log if l.Category  == 'Error' and l.Type not in ('Lickometer', 'Nosepoke')]

    if len(errors) > 0:
      print('%d errors' % len(errors))

    warnings = [l for l in log if l.Notes.startswith('Unregistered tag') or l.Notes.startswith('Presence signal')]

    if len(warnings) > 0:
      print('%d warnings in logs' % len(warnings))
      notes = collections.Counter(l.Notes for l in warnings)
      for note, n in sorted(notes.items()):
        print("%s: %d time(s)" % (note, n))

    return () #dummy return to keep _logAnalysis happy


class PresenceLogAnalyzer(object):
  """
  Class of objects validating data against 'Presence' warnings using
  a sophisticated heuristic.

  The 'Presence signal without antenna registration.' warning might indicate
  that either an antenna is not working properly or a mouse has its transponder
  lost.
  """
  def __init__(self):
    self.notes = '\n'.join(['Generated by PresenceLogAnalyzer', '', ''])
    self.finBin = 3600. # Final bins: 1 hour

  def __call__(self, md):
    results = []
    log = md.getLog(order='DateTime')
    for cage in md.getInmates():
      for corner in range(1, 5):
        # XXX: idea - get timestamps from md._Data_logDateTime
        tt = np.array([toTimestampUTC(l.DateTime) for l in log \
                       if l.Cage == cage and l.Corner == corner and l.Notes.startswith('Presence signal')])
        if len(tt) > 0:
          # print('%s\t%s\t%s' % (cage, corner, len(events)))
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
          idcs = np.where(tds < 30.)[0]
          tt = np.delete(tt, np.unique(np.array([idcs, idcs+1])))
          # XXX: czy to spowoduje, ze ciag bledow pozostanie niezauwazony???

          if len(tt) > 0:
            # Wywalamy jesli izolowany
            tds = np.diff(tt)
            mask = np.zeros_like(tt)
            mask[0] += 0.5
            mask[-1] += 0.5
            idcs2 = np.where(tds > 1800.)[0]
            mask[idcs2] += 0.5
            mask[idcs2 + 1] += 0.5
            tt = np.delete(tt, np.where(mask > 0.75))

          if len(tt) > 0:
            # Pomijamy jesli <= 4 bledy w dobie
            ttMin = tt.min()
            span = tt.max() - ttMin
            nBins = ceil(span / (24 * 3600.))
            longBins = np.linspace(ttMin, ttMin + nBins * 24 * 3600.,
                                   int(nBins) + 1)
            hist, _ = np.histogram(tt, bins=longBins)
            print(tt)
            print(longBins)
            print(hist)
            if (hist > 4).any():
              # print('%s\t%s\t%s\t%s' % (cage, corner, 'Zostalo ', len(tt)))
              nBins = ceil(span / self.finBin)
              bins = np.arange(ttMin, ttMin + nBins * self.finBin,
                               int(nBins) + 1)
              hist, _ = np.histogram(tt, bins=bins)
              idcs = mmlab.contiguous_regions(hist)
              for tstartidx, tstopidx in idcs:
                tstart = bins[tstartidx]
                tstop = bins[tstopidx]
                results.append(ExcludeMiceData(startTime=datetime.fromtimestamp(tstart, UTC),
                        endTime=datetime.fromtimestamp(tstop, UTC),
                        logType='Presence',
                        cage=cage, corner=corner,
                        notes=str(sum(hist[tstartidx:tstopidx]))
                        + ' cases. ' + self.notes))

    return tuple(results)


def overlap(exc, interval):
  """
  Check whether the time interval definded in exc
  (exc.startTime to exc.endTime) has non-zero overlap
  with time interval given as the second argument.
  """
  start, end = interval
  return start <= exc.startTime < end or\
         start < exc.endTime <= end or\
         exc.startTime <= start and exc.endTime >= end


class TestMiceData(object):
  """
  Class of objects for checking whether report generated by :py:class:`DataValidator`
  objects confirms validity of given scope of data.
  """
  def __init__(self, issue=None):
    """
    :param issue: type of the invalidating issue
    :type issue: basestring
    """
    if issue is not None:
      self._issue = issue

  def __call__(self, report, interval, **kwargs):
    """
    :param report: report generated by :py:class:`DataValidator`
    :type report: collection(:py:class:`ExcludeMiceData`, ...)

    :param interval: boundaries of temporal scope of validated data
    :type interval: (:py:class:`datetime.datetime`, :py:class:`datetime.datetime`)

    :keyword cage: cage to which the scope of data is restricted
    :type cage: int

    :keyword corner: corner to which the scope of data is restricted
    :type corner: int

    :keyword side: side to which the scope of data is restricted
    :type side: int

    :return: ``True`` if the scope of data is valid else ``False``
    :rtype: bool
    """
    for excluded in report:
      if not self._single_test(excluded, interval, **kwargs):
        return False

    return True

  def _single_test(self, exc, interval, **kwargs):
    """
    Perform a test on a single ExcludeMiceData object
    """
    if exc.logType == self._issue and overlap(exc, interval):
      for key, value in kwargs.items():
        try:
          if value != exc.location[key]:
            return True

        except KeyError:
          pass

      return False

    return True


class TestLickometer(TestMiceData):
  """
  Class of objects for checking whether report generated by :py:class:`DataValidator`
  objects confirms validity of lickometer reports within given scope of data.
  """
  _issue = 'Lickometer'


class TestPresence(TestMiceData):
  """
  Class of objects for checking whether report generated by :py:class:`DataValidator`
  objects confirms validity of visit detection within given scope of data.
  """
  _issue = 'Presence'

