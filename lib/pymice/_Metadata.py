#!/usr/bin/env python
# encoding: utf-8
###############################################################################
#                                                                             #
#    PyMICE library                                                           #
#                                                                             #
#    Copyright (C) 2013-2017 Jakub M. Dzik a.k.a. Kowalski, S. Łęski          #
#    (Laboratory of Neuroinformatics; Nencki Institute of Experimental        #
#    Biology of Polish Academy of Sciences)                                   #
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
from datetime import datetime
import csv
import re

try:
  from ConfigParser import RawConfigParser, NoSectionError, NoOptionError

except ImportError:
  from configparser import RawConfigParser, NoSectionError, NoOptionError

import pytz
import matplotlib.ticker
import matplotlib.dates as mpd

from ._Tools import convertTime, warn, isString, deprecatedAlias


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




class Timeline(RawConfigParser, matplotlib.ticker.Formatter):
  """
  A class of objects for loading experiment timeline definition files.

  As a subclass of :py:class:`matplotlib.ticker.Formatter` the class is also
  time axis formatter in :py:mod:`matplotlib.dates` coordinates.

  **File format description**

  The format is a constrained INI format. Every section defined corresponds to
  phase of same name. The minimal information required about a phase are its
  boundaries given as ``start`` and ``end`` properties in format
  ``YYYY-MM-DD HH:MM`` or ``YYYY-MM-DD HH:MM:SS``. Optional information about
  timezone of ``start`` and ``end`` properties might be provided by ``tzinfo``
  property (name of timezone defined in :py:mod:`pytz` module).
  """
  def __init__(self, path, fname=None, tzinfo=None):
    """
    Read the description of the experiment timeline.

    :param path: a path to either the experiment timeline file or a directory
                 containing experiment timeline file of either ``fname``
                 or `'config.txt'` or `'config*.(txt|ini)'` name (matching in
                 that order).
    :type path: basestring

    :param fname: name of the experiment timeline file in ``path`` directory
    :type fname: basestring or None

    :param tzinfo: default timezone
    :type tzinfo: :py:class:`datetime.tzinfo`
    """
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

  def getTimeBounds(self, phases):
    """
    :param phases: name(s) of phase(s)
    :type phases: [basestring, ...] or basestring

    :return: timezone-aware boundaries of minimal period of time covering
             all phases given
    :rtype: (:py:class:`datetime.datetime`, :py:class:`datetime.datetime`)
    """

    if isString(phases):
      try:
        tzinfo = pytz.timezone(self.get(phases, 'tzinfo'))

      except (NoOptionError, pytz.UnknownTimeZoneError):
        tzinfo = self.tzinfo

      times = []
      for option in ('start', 'end'):
        t = convertTime(self.get(phases, option), tzinfo)

        times.append(t)

      if times[0] > times[1]:
        warn.warn("Phase %s starts after it ends (%s > %s)" % (phases, times[0], times[1]))

      return tuple(times)
        
    else:
      starts = []
      ends = []
      for ss in phases:
        st, et = self.getTimeBounds(ss)
        starts.append(st)
        ends.append(et)

      return min(starts), max(ends)

  def __call__(self, x, pos=0):
    x = mpd.num2date(x)
    for sec in self.sections():
      t1, t2 = self.getTimeBounds(sec)
      if t1 <= x and x < t2:
        return sec

    return 'Unknown'

  getTime = deprecatedAlias(getTimeBounds)


class ExperimentTimeline(Timeline):
  def __init__(self, *args, **kwargs):
    warn.deprecated('Class ExperimentTimeline is deprecated; use Timeline class instead')
    super(ExperimentTimeline, self).__init__(*args, **kwargs)
