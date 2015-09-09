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

import sys
import os 
from datetime import datetime
import csv
import re

try:
  from ConfigParser import RawConfigParser, NoSectionError, NoOptionError

except ImportError:
  from configparser import RawConfigParser, NoSectionError, NoOptionError

import pytz 
import numpy as np                                           
import matplotlib.ticker
import matplotlib.dates as mpd
import matplotlib.pyplot as plt

from ._Tools import convertTime, warn

if sys.version_info >= (3, 0):
  basestring = str


class MetadataNode(object):
  _labels = None
  _filename = None
  _nextClass = None

  @classmethod
  def fromMeta(cls, meta, **kwargs):
    _next = None if cls._nextClass is None else cls._nextClass.fromMeta(meta)
    filename = os.path.join(meta, cls._filename)
    return cls.fromCSV(filename, _next=_next, **kwargs)

  @classmethod
  def fromCSV(cls, filename, **kwargs):
    if not os.path.exists(filename):
      return

    result = {}
    with open(filename, 'rb') as fh:
      for row in csv.DictReader(fh):
        byLabel = [row.pop(x, '').strip() for x in cls._labels]
        for k, v in kwargs.items():
          assert k not in row
          row[k] = v

        instance = cls(*byLabel, **row)
        result[instance.Name] = instance

    return result

  def __repr__(self):
    return str(self)

  def __str__(self):
    return unicode(self).encode('utf-8')

  def __unicode__(self):
    return self.Name


class Substance(MetadataNode):
  _labels = ['name', 'molar mass', 'density']
  _filename = 'substances.csv'
  
  def __init__(self, Name, MolarMass, Density, _next=None):
    self.Name = Name.decode('utf-8').lower()
    self.MolarMass = float(MolarMass) if MolarMass != '' else None
    self.Density = float(Density) if Density != '' else None


class Concentration(object):
  def __init__(self, Substance, Amount=None, Unit=None, VolumeConcentration=None, MassFraction=None):
    self.Substance = Substance
    self.Amount = Amount
    self.Unit = Unit.decode('utf-8') if Amount is not None and Unit is not None else None
    self.VolumeConcentration = VolumeConcentration
    self.MassFraction = MassFraction

  def __repr__(self):
    return str(self)

  def __str__(self):
    return unicode(self).encode('utf-8')

  def __unicode__(self):
    if self.Amount is None:
      return unicode(self.Substance)

    if self.Unit is None:
      return u'%s %f' % (self.Substance, self.Amount)

    return u'%s %f [%s]' % (self.Substance, self.Amount, self.Unit)


class Solutes(object):
  def __init__(self, solutes, density=None):
    self.__keys = set()

    for substance, amount, unit in solutes:
      massFraction = None
      volumeConcentration = None
      if unit == 'volume':
        volumeConcentration = amount
        try:
          massFraction = amount * substance.Density / density

        except:
          pass

      if unit == 'mass':
        massFraction = amount
        try:
          volumeConcentration = amount * density / substance.Density

        except:
          pass

      name = unicode(substance)
      self.__keys.add(name)
      setattr(self, name,
              Concentration(substance, amount, unit,
                        VolumeConcentration=volumeConcentration,
                        MassFraction=massFraction))

  def __bool__(self):
    return len(self.__keys) > 0

  def __len__(self):
    return len(self.__keys)

  def keys(self):
    return list(self.__keys)

  def __getitem__(self, key):
    return getattr(self, key)

  def __contains__(self, substance): 
    return unicode(substance) in self.__keys

  def __repr__(self):
    return str(self)

  def __str__(self):
    return unicode(self).encode('utf-8')

  def __unicode__(self):
    return u', '.join(unicode(getattr(self, k)) for k in sorted(self.__keys))

          


class Liquid(MetadataNode):
  _filename = 'liquids.csv'
  _labels = ['name', 'density']
  __parseSubstance = re.compile('^\s*(?P<substance>\S+)(?:\s+\[(?P<unit>\w+)\])?\s*$')
  _nextClass = Substance

  def __init__(self, Name, Density, _next=None, **solutes):
    self.Name = Name.decode('utf-8').lower()
    self.Density = float(Density) if Density != '' else None
    self.Solvent = None

    tmp = []
    for key, amount in solutes.items():
      match = self.__parseSubstance.match(key.lower())
      if not match:
        continue

      substance, unit = match.group('substance', 'unit')
      substance = substance.strip().lower()
      if unit is not None:
        unit = unit.strip().lower()

      amount = amount.strip().lower()
      if amount in ('medium', 'solvent'):
        assert self.Solvent is None
        self.Solvent  = _next.get(substance, substance) if _next else substance

      else:
        try:
          amount = float(amount)

        except:
          continue

        tmp.append((_next.get(substance, substance) if _next else substance,
                    amount,
                    unit))

    if len(tmp) == 1. and not self.Solvent:
      substance, amount, unit = tmp.pop()
      self.Solvent = Concentration(substance, amount, unit,
                                   MassFraction=1.,
                                   VolumeConcentration=1.)

    elif self.Solvent and not tmp:
      self.Solvent = Concentration(substance,
                                   MassFraction=1.,
                                   VolumeConcentration=1.)

    self.Solutes = Solutes(tmp, density=self.Density)

    if self.Solvent:
      massFraction = 1.
      volumeConcentration = None
      if self.Solutes:
        try:
          for solute in self.Solutes.keys():
            massFraction -= self.Solutes[solute].MassFraction

        except:
          massFraction = None

        try:
          volumeConcentration = massFraction * self.Density / self.Solvent.Density

        except:
          pass

        self.Solvent = Concentration(self.Solvent,
                                     VolumeConcentration=volumeConcentration,
                                     MassFraction=massFraction)

      if not self.Solutes and hasattr(self.Solvent.Substance, 'Density'):
        if self.Density is None:
          self.Density = self.Solvent.Substance.Density

        else:
          assert self.Density == self.Solvent.Substance.Density or self.Solvent.Substance.Density is None

  def __contains__(self, substance):
    if self.Solvent and unicode(self.Solvent.Substance) == unicode(substance):
      return True

    return self.Solutes and substance in self.Solutes

#  @classmethod
#  def fromCSV(cls, filename, substances=None):
#    result = {}
#    with open(filename, 'rb') as fh:
#      #return dict((cls._key(row), cls(*map(row.get, cls._labels)))\
#      #            for row in csv.DictReader(fh))
#      for row in csv.DictReader(fh):
#        key = cls._key(row)
#        byLabel = map(row.pop, cls._labels)
#        result[key] = cls(*byLabel, substances=substances, **row)
#
#    return result
#
#  @classmethod
#  def fromMeta(cls, meta):
#    filename = os.path.join(meta, cls._filename)
#    return cls.fromCSV(filename, Substance.fromMeta(meta))

  def __repr__(self):
    result = str(self.Name)
    if self.Solutes:
      result += ': %s' % str(self.Solutes)

      if self.Solvent:
        result += ' in %s' % str(self.Solvent.Substance)

    else:
      result += ': %s' % str(self.Solvent.Substance)

    return result


class Bottles(MetadataNode):
  _filename = 'bottles.csv'
  _labels = ['name']
  _nextClass = Liquid
  __parseLocation = re.compile('^\s*(?P<kind>corner|side)\s*(?P<number>\d+)\s*$')

  def __init__(self, Name, _next=None, **locations):
    self.Name = Name.decode('utf-8').lower()
    self.Corners = {}
    self.Sides = {}

    for key, liquid in locations.items():
      liquid = liquid.strip().lower()
      liquid = _next.get(liquid, liquid) if _next else liquid
      match = self.__parseLocation.match(key.lower())
      kind, number = match.group('kind', 'number')
      number = int(number)
      if kind == 'corner':
        self._addCorner(number, liquid)

      elif kind == 'side':
        self._addSide(number, liquid)

  def _addSide(self, side, liquid):
    assert side not in self.Sides
    self.Sides[side] = liquid

  def _addCorner(self, corner, liquid):
    assert corner not in self.Corners
    self._addSide(corner * 2 - 1, liquid)
    self._addSide(corner * 2, liquid)
    self.Corners[corner] = liquid


class Animal(MetadataNode):
  _filename = 'animals.csv'
  _labels = ['name', 'weight', 'deceased'] 

  def __init__(self, Name, Weight=None, Deceased=None, _next=None, _groups=None, _partitions=None, **kwargs):
    self.Name = Name.decode('utf-8')
    self.Weight = float(Weight) if Weight != '' else None
    self.Deceased = Deceased if Deceased != '' else False
    for key, value in kwargs.items():
      key = key.strip().lower()
      value = value.strip().lower()

      if key.startswith('group'):
        if _groups is not None:
          if key == 'group':
            group = value

          else:
            if value == '':
              continue

            group = key[5:].strip()

          try:
            _groups[group].append(self)

          except KeyError:
            _groups[group] = [self]

      elif key.startswith('partition'):
        if _partitions is not None:
          key = key[9:].strip()
          value = int(value)

          try:
            _partitions[key][value].append(self)

          except KeyError:
            try:
              _partitions[key][value] = [self]

            except KeyError:
              _partitions[key] = {value: [self]}


class Phase(MetadataNode):
  _filename = 'phases.csv'
  _labels = ['start', 'end', 'name', 'type', 'iteration', 'partition', 'comments']

  def __init__(self, Start, End, Name, Type, Iteration, Partition, Comments, _partitions, _bottles, tzinfo=None, **kwargs):
    self.Start = convertTime(Start, tzinfo)
    self.End = convertTime(End, tzinfo)
    self.Name = Name.decode('utf-8') if Name != '' else None

    if self.End < self.Start:
      warn.warn("Phase %s starts after it ends (%s > %s)" % (self.Name, self.Start, self.End))

    self.Type = Type.decode('utf-8') if Type != '' else None
    self.Iteration = int(Iteration) if Iteration != '' else None
    self.Mice = _partitions[Partition]
    self.Comments = Comments.decode('utf-8') if Comments != '' else None
    self.Bottles = {}
    for key, val in kwargs.items():
      key = key.strip().lower()
      val = val.strip().lower()
      if key.startswith('cage') and val in _bottles:
        cage = int(key[4:].strip())
        self.Bottles[cage] = _bottles[val]
      
  @classmethod
  def fromCSV(cls, filename, tzinfo=None, **kwargs):
    if not os.path.exists(filename):
      return

    result = {}
    rows = {}
    with open(filename, 'rb') as fh:
      for i, row in enumerate(csv.DictReader(fh)):
        byLabel = [row.pop(x, '').strip().lower() for x in cls._labels]
        for k, v in kwargs.items():
          assert k not in row
          row[k] = v

        if tzinfo is not None:
          row['tzinfo'] = tzinfo

        instance = cls(*byLabel, **row)
        if instance.Name is not None:
          if instance.Name in result:
            warn.warn("Phase %s already defined - owerwriting!" % instance.Name)

          result[instance.Name] = instance

        else:
          rows[i] = instance

    for i, instance in rows.items():
      if instance.Type is not None and instance.Iteration is not None:
        name = "%s %d" % (instance.Type, instance.Iteration)
        if name in result:
          j = 0
          while ("%s (%d)" % (name, j)) in result:
            j += 1

          name = "%s (%d)" % (name, j)

        instance.Name = name
        result[instance.Name] = instance
        del rows[i]

    for i, instance in rows.items():
      if instance.Type is not None:
        j = 0
        while ("%s (%d)" % (instance.Type, j)) in result:
          j += 1

        instance.Name = "%s (%d)" % (instance.Type, j)
        result[instance.Name] = instance
        del rows[i]

    for i, instance in rows.items():
      name = "Phase %d" % i
      if name in result:
        j = 0
        while ("%s (%d)" % (name, j)) in result:
          j += 1

        name = "%s (%d)" % (name, j)

      instance.Name = name
      result[instance.Name] = instance

    return result

  @classmethod
  def fromMeta(cls, meta, tzinfo=None, **kwargs):
    bottles = Bottles.fromMeta(meta)
    groups = {}
    partitions = {}
    animals = Animal.fromMeta(meta, _groups=groups, _partitions=partitions)
    phases = cls.fromCSV(os.path.join(meta, cls._filename),
                         _partitions=partitions,
                         _bottles=bottles,
                         tzinfo=tzinfo)
    return phases, animals, groups




class ExperimentTimeline(RawConfigParser, matplotlib.ticker.Formatter):
  def __init__(self, path, fname=None, tzone=None, tzinfo=None): 
    self.tzone = pytz.timezone('CET') if tzone is None else tzone
    self.tzinfo = tzinfo

    RawConfigParser.__init__(self)
    if fname is None:
      if os.path.isfile(path):
        self.path = path

      elif os.path.isfile(os.path.join(path, 'config.txt')):
        self.path = os.path.join(path, 'config.txt')

      else:
        self.path = filter(lambda x: x.startswith('config') \
                           and (x.endswith('.txt') or x.endswith('.ini')),
                           os.listdir(path))[0]

    else:
      self.path = os.path.join(path, fname)

    self.read(self.path)
      
  def gettime(self, sec): 
    warn.deprecated('Deprecated method gettime() called; use getTime() instead.')
    return self.getTime(sec)

  def getTime(self, sec): 
    """
    Convert start and end time and date read from section sec (might be a list)
    of the config file to a tuple of times from epoch.
    """

    if isinstance(sec, basestring):
      try:
        tzinfo = pytz.timezone(self.get(sec, 'tzinfo'))

      except (NoOptionError, pytz.UnknownTimeZoneError):
        tzinfo = self.tzinfo

      times = []
      for option in ('start', 'end'):
        try:
          value = self.get(sec, option)

        except NoOptionError:
          day, month, year = self.get(sec, option + 'date').split('.')
          time = self.get(sec, option + 'time').split(':')
          ts = map(int, [year, month, day] + time)
          t = datetime(*ts, **{'tzinfo': tzinfo})

          warn.deprecated('Deprecated options %sdate and %stime used, use %s instead.' %\
                     (option, option, option))

        else:
          t = convertTime(value, tzinfo)

        times.append(t)

      if times[0] > times[1]:
        warn.warn("Phase %s starts after it ends (%s > %s)" % (sec, times[0], times[1]))

      return tuple(times)
        
    else:
      starts = []
      ends = []
      for ss in sec:
        st, et = self.getTime(ss)
        starts.append(st)
        ends.append(et)

      return min(starts), max(ends)

  def __call__(self, x, pos=0):
    x = mpd.num2date(x)
    for sec in self.sections():
      t1, t2 = self.gettime(sec)
      if t1 <= x and x < t2:
        return sec

    return 'Unknown'    
  
  def mark(self, sec, ax=None):
    """Mark given phases on the plot"""
    if ax is None:
      ax = plt.gca()

    ylims = ax.get_ylim()
    for tt in self.gettime(sec):
      ax.plot([mpd.date2num(tt),] * 2, ylims, 'k:')

    plt.draw()
  
  def plot_nights(self, *args, **kwargs):
    warn.deprecated('Deprecated method plot_nights() called; use plotNights() instead.')
    return self.plotNights(*args, **kwargs)

  def plotNights(self, sections, ax=None):
    """Plot night from sections"""
    if ax is None:
      ax = plt.gca()

    #xlims = ax.get_xlim()
    if type(sections) == str:
      sections = [sections]

    for sec in sections:
      t1, t2 = self.gettime(sec)
      ax.axvspan(mpd.date2num(t1), mpd.date2num(t2),
                 color='0.8', alpha=0.5, zorder=-10)

    #ax.set_xlim(xlims)
    plt.draw()

  def plot_sections(self):
    warn.deprecated('Deprecated method plot_sections() called; use plotSections() instead.')
    return self.plotSections()

  def plotSections(self):
    """Diagnostic plot of sections defined in the config file."""
    figg = plt.figure()                         
    for idx, sec in enumerate(self.sections()):
      t1, t2 = mpd.date2num(self.gettime(sec)) #cf2time(cf, sec)
      plt.plot([t1, t2], [idx, idx], 'ko-') 
      plt.plot([t2], [idx], 'bo')
      plt.text(t2 + 0.5, idx, sec)

    ax = plt.gca()
    ax.xaxis.set_major_locator(mpd.HourLocator(np.array([00]), 
                                               tz=self.tzone)) 
    ax.xaxis.set_major_formatter(mpd.DateFormatter('%d.%m %H:%M', tz=self.tzone))
    ax.autoscale_view()
    ax.get_figure().autofmt_xdate()
    plt.title(self.path) 
    plt.draw()


class ExperimentConfigFile(ExperimentTimeline):
  def __init__(self, *args, **kwargs):
    warn.deprecated('Deprecated class ExperimentConfigFile used; use ExperimentTimeline instead.')
    ExperimentTimeline.__init__(self, *args, **kwargs)
