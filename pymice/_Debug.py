#!/usr/bin/env python
# encoding: utf-8
###############################################################################
#                                                                             #
#    PyMICE library                                                           #
#                                                                             #
#    Copyright (C) 2013-2015 Jakub M. Kowalski, S. Łęski (Laboratory of       #
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

import operator

from datetime import timedelta
from math import sqrt, ceil

import numpy as np
import matplotlib.ticker
import matplotlib.dates as mpd
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.path import Path

import dateutil.tz


from ._Tools import mergeIntervalsValues, groupBy



def plotLimits(ec, sections, ax=None, color='k', linestyle=':', **kwargs):
  """Mark given phases on the plot"""
  if ax is None:
    ax = plt.gca()

  for tt in ec.getTime(sections):
    ax.axvline(mpd.date2num(tt), color=color, linestyle=linestyle, **kwargs)

  plt.draw()

def plotNights(ec, sections, ax=None, color='0.8', alpha=0.5, zorder=-10, **kwargs):
  """Plot sections as nights"""
  if ax is None:
    ax = plt.gca()

  #xlims = ax.get_xlim()
  if type(sections) == str:
    sections = [sections]

  for sec in sections:
    t1, t2 = ec.getTime(sec)
    ax.axvspan(mpd.date2num(t1), mpd.date2num(t2),
               color=color, alpha=alpha, zorder=zorder, **kwargs)

  #ax.set_xlim(xlims)
  plt.draw()


def plotPhases(ec, tzone=None, ax=None):
  """Diagnostic plot of sections defined in the config file."""
  if tzone is None:
    tzone = dateutil.tz.tzlocal()

  sections = ec.sections()

  fig = None
  if ax is None:
    fig = plt.figure()
    ax = fig.add_subplot(1, 1, 1)
    ax.set_title(ec.path) 
    ax.set_xlim(*mpd.date2num(ec.getTime(sections)))
    ax.set_ylim(-1, len(sections))

    locator = mpd.AutoDateLocator(tz=tzone)
    formatter = mpd.AutoDateFormatter(locator, tz=tzone)
    ax.xaxis.set_major_locator(locator)
                               #mpd.HourLocator([0], 
                               #                tz=tzone)) 
    ax.xaxis.set_major_formatter(formatter)
                                 #mpd.DateFormatter('%d.%m %H:%M',
                                 #                  tz=tzone))
    ax.autoscale_view()
    ax.get_figure().autofmt_xdate()
    #plt.draw()

  for idx, sec in enumerate(sections):
    t1, t2 = mpd.date2num(ec.getTime(sec))
    ax.plot([t1, t2], [idx, idx], 'ko-') 
    ax.plot([t2], [idx], 'bo')
    ax.text(t2 + 0.5, idx, sec,
            verticalalignment="center",
            horizontalalignment="left")

  if fig is not None:
    fig.canvas.draw()

  return fig


def _plotEnv(rawData, ax, env, **kwargs):
  data = mergeIntervalsValues(rawData,
                              ('DateTime',
                               'DateTime',
                               env),
                               mergeWindow=timedelta(0, 120))
  xs = mpd.date2num([t for row in data for t in row[:2]])
  ys = [y for _, _, (y,) in data for _ in xrange(2)]
  ax.plot(xs, ys, **kwargs)

  return min(xs), max(xs), min(ys), max(ys)


def plotEnv(md, env='Illumination', ax=None, cages=None, start=None, end=None, label=False, tzone=None, **kwargs):
  envData = md.getEnvironment(start=start, end=end)
  if len(envData) == 0:
    return

  byCages = groupBy(envData, operator.attrgetter('Cage'))
  if cages is None:
    cages = set(byCages)

  elif isinstance(cages, basestring):
    cages = {int(cages)}

  else:
    try:
      cages = set(cages)

    except:
      cages = {int(cages)}

  cages = sorted(set(byCages) & cages)

  if len(cages) == 0:
    return

  fig = None
  if ax is None:
    fig = plt.figure()
    fig.suptitle(env)
    width = int(ceil(sqrt(len(cages))))
    height = int(ceil(float(len(cages)) / width))

    for i, cage in enumerate(cages, 1):
      ax = fig.add_subplot(height, width, i)
      ax.set_title("cage %d" % cage) 

      locator = mpd.AutoDateLocator(tz=tzone)
      formatter = mpd.AutoDateFormatter(locator, tz=tzone)
      ax.xaxis.set_major_locator(locator)
      ax.xaxis.set_major_formatter(formatter)

      xmin, xmax, ymin, ymax = _plotEnv(byCages[cage], ax, env, **kwargs)
      ax.set_xlim(xmin, xmax)
      ax.set_ylim(ymin - 1, ymax + 1)
      plt.xticks(rotation=30) # -_-
      ax.autoscale_view()

    #fig.autofmt_xdate()
    fig.tight_layout()
    fig.canvas.draw()
    return fig
  
  for cage in sorted(cages):
    if label:
      _plotEnv(byCages[cage], ax, env, label="cage %d" % cage, **kwargs)

    else:
      _plotEnv(byCages[cage], ax, env, **kwargs)


def _plotVisitPeriods(ax, rawData, start, end, top, bottom, window,
                      color, linestyle, label=None, **kwargs):
  data = mergeIntervalsValues(rawData,
                              ('Start',
                               'End'),
                               overlap=True,
                               mergeWindow=timedelta(0, window))

  xs = []
  ys = []
  if start is not None:
    xs.append(start)
    ys.append(bottom)

  for s, e, _ in data:
    xs.extend([s, s, e, e])
    ys.extend([bottom, top, top, bottom])

  if end is not None:
    xs.append(end)
    ys.append(bottom)

  xs = mpd.date2num(xs)
  ax.plot(xs, ys, color=color, linestyle=linestyle, label=label, **kwargs)
  mid = 0.5 * (top + bottom)
  xmin, xmax = min(xs), max(xs)
  ax.plot([xmin, xmax], [mid, mid], color=color, linestyle=':' if linestyle != ':' else '--', **kwargs)
  return xmin, xmax

  #for row in data:
  #  s, e = mpd.date2num(row[:2])
  #  codes = [Path.MOVETO, Path.LINETO, Path.LINETO, Path.LINETO, Path.CLOSEPOLY]
  #  verts = [(s, 1), (e, 1), (e, 0), (s, 0), (s, 1)]
  #  path = Path(verts, codes)
  #  patch = patches.PathPatch(path, facecolor='none', edgecolor='red')
  #  ax.add_patch(patch)


def plotVisitPeriods(md, window=60, ax=None, cages=None, start=None, end=None,
                     tzone=None, label=False, color='b', linestyle='-',
                     **kwargs):
  visits = md.getVisits(start=start, end=end)
  if len(visits) == 0:
    return

  byCages = groupBy(visits, operator.attrgetter('Cage'))
  if cages is None:
    cages = set(byCages)

  elif isinstance(cages, basestring):
    cages = {int(cages)}

  else:
    try:
      cages = set(cages)

    except:
      cages = {int(cages)}

  cages = sorted(set(byCages) & cages)

  if len(cages) == 0:
    return

  fig = None
  if ax is None:
    fig = plt.figure()
    fig.suptitle('Visits detected')
    width = int(ceil(sqrt(len(cages))))
    height = int(ceil(float(len(cages)) / width))

    for i, cage in enumerate(cages, 1):
      ax = fig.add_subplot(height, width, i)
      ax.set_title("cage %d" % cage) 

      locator = mpd.AutoDateLocator(tz=tzone)
      formatter = mpd.AutoDateFormatter(locator, tz=tzone)
      ax.xaxis.set_major_locator(locator)
      ax.xaxis.set_major_formatter(formatter)

      xmin, xmax = _plotVisitPeriods(ax, byCages[cage], start, end, 0.9, 0.1,
                                     window, color, linestyle, **kwargs)

      ax.set_xlim(xmin, xmax)
      ax.set_ylim(0, 1)
      plt.xticks(rotation=30) # -_-
      ax.autoscale_view()

    #fig.autofmt_xdate()
    fig.tight_layout()
    fig.canvas.draw()
    return fig
  
  for i, cage in enumerate(sorted(cages)):
    if label:
      _plotVisitPeriods(ax, byCages[cage], start, end, i + 0.9, i + 0.1, window,
                        color, linestyle, label='cage %d' % cage, **kwargs)

    else:
      _plotVisitPeriods(ax, byCages[cage], start, end, i + 0.9, i + 0.1, window,
                        color, linestyle, **kwargs)



def plotData(mds):
  """Diagnostic plot of data from multiple sources"""
  fig = plt.figure()
  ax = fig.add_subplot(1, 1, 1)
  limits = sorted([(md.getStart(), md.getEnd()) for md in mds])
  for idx, (t1, t2) in enumerate(limits):
    if t1 is not None and t2 is not None:
      t1, t2 = mpd.date2num((t1, t2))

    ax.plot([t1, t2], [idx, idx], 'ko-') 
    ax.plot([t2], [idx], 'bo')

  ax.xaxis.set_major_locator(mpd.HourLocator(np.array([00]), 
                                             tz=self.tzone)) 
  ax.xaxis.set_major_formatter(mpd.DateFormatter('%d.%m %H:%M', tz=self.tzone))
  ax.autoscale_view()
  ax.get_figure().autofmt_xdate()
  ax.set_title(ec.path) 
  plt.draw()

def checkData(mds):
  """Check for recording gaps"""
  limits = sorted([(md.getStart(), md.getEnd()) for md in mds])
  for ((_, a), (b, _)) in zip(limits[:-1], limits[1:]):
    print('%s               %s' % (1, b - a))

def plotCumulativeVisits(md, tzone=None, **kwargs):
  fig = plt.figure()
  ax = fig.add_subplot(1, 1, 1)
  visits = md.getVisits(order='Start')
  ax.plot(mpd.date2num(map(operator.attrgetter('Start'), visits)),
          range(len(visits)))

  locator = mpd.AutoDateLocator(tz=tzone)
  formatter = mpd.AutoDateFormatter(locator, tz=tzone)
  ax.xaxis.set_major_locator(locator)
  ax.xaxis.set_major_formatter(formatter)

  ax.autoscale_view()
  ax.get_figure().autofmt_xdate()
  plt.draw()
  return ax

def plotOffsetToUTC(timePoints, ax=None, **kwargs):
  if ax is None:
    ax = plt.gca()

  utcOffsetHours = [t.tzinfo.utcoffset(t).total_seconds() / 3600. for t in timePoints]
  ax.scatter(mpd.date2num(timePoints), utcOffsetHours, **kwargs)
