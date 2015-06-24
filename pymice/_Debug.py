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

import matplotlib.ticker
import matplotlib.dates as mpd
import matplotlib.pyplot as plt

from ._Tools import deprecated



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


def plotPhases(ec):
  """Diagnostic plot of sections defined in the config file."""
  fig = plt.figure()
  ax = fig.add_subplot(1, 1, 1)
  for idx, sec in enumerate(ec.sections()):
    t1, t2 = mpd.date2num(ec.getTime(sec))
    ax.plot([t1, t2], [idx, idx], 'ko-') 
    ax.plot([t2], [idx], 'bo')
    ax.text(t2 + 0.5, idx, sec)

  ax.xaxis.set_major_locator(mpd.HourLocator(np.array([00]), 
                                             tz=self.tzone)) 
  ax.xaxis.set_major_formatter(mpd.DateFormatter('%d.%m %H:%M', tz=self.tzone))
  ax.autoscale_view()
  ax.get_figure().autofmt_xdate()
  ax.set_title(ec.path) 
  plt.draw()


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
    print 1, '             ', b - a

def plotCumulativeVisits(md, **kwargs):
  fig = plt.figure()
  ax = fig.add_subplot(1, 1, 1)
  visits = md.getVisits(order='Start')
  ax.plot(mpd.date2num(map(operator.attrgetter('Start'), visits)),
          range(len(visits)))

  ax.xaxis.set_major_locator(mpd.HourLocator(np.array([00]), 
                                             tz=self.tzone)) 
  ax.xaxis.set_major_formatter(mpd.DateFormatter('%d.%m %H:%M', tz=self.tzone))
  ax.autoscale_view()
  ax.get_figure().autofmt_xdate()
  ax.set_title(ec.path) 
  plt.draw()
  return ax

def plotIllumination(md, **kwargs):
  fig = plt.figure()
  ax = fig.add_subplot(1, 1, 1)
  env = md.getEnvironment(order='DateTime')
  ax.plot(mpd.date2num(map(operator.attrgetter('DateTime'), env)),
          map(operator.attrgetter('Illumination'), env))

  ax.xaxis.set_major_locator(mpd.HourLocator(np.array([00]), 
                                             tz=self.tzone)) 
  ax.xaxis.set_major_formatter(mpd.DateFormatter('%d.%m %H:%M', tz=self.tzone))
  ax.autoscale_view()
  ax.get_figure().autofmt_xdate()
  ax.set_title(ec.path) 
  plt.draw()
  return ax
