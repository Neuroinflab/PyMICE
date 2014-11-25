#!/usr/bin/env python
# encoding: utf-8
"""
ggg
"""
# Marysia_ARC/main.py

import os 
import time
import datetime
import csv
import re
import collections

from ._Loader import convertTime



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
        byLabel = [row.pop(x, '').strip().lower() for x in cls._labels]
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
    self.Name = unicode(Name).lower()
    self.MolarMass = float(MolarMass) if MolarMass != '' else None
    self.Density = float(Density) if Density != '' else None


class Concentration(object):
  def __init__(self, Substance, Amount=None, Unit=None, VolumeConcentration=None, MassFraction=None):
    self.Substance = Substance
    self.Amount = Amount
    self.Unit = unicode(Unit) if Amount is not None and Unit is not None else None
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
    self.Name = unicode(Name).lower()
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
  __parseLocation = re.compile('^\s*(?P<kind>\S+)\s+(?P<number>\d+)\s*$')

  def __init__(self, Name, _next=None, **locations):
    self.Name = unicode(Name).lower()
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
    self.Name = unicode(Name)
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

  def __init__(self, Start, End, Name, Type, Iteration, Partition, Comments, _partitions, _bottles, **kwargs):
    self.Start = convertTime(Start)
    self.End = convertTime(End)
    self.Name = Name if Name != '' else None
    self.Type = Type if Type != '' else None
    self.Iteration = int(Iteration) if Iteration != '' else None
    self.Mice = _partitions[Partition]
    self.Comments = Comments if Comments != '' else None
    self.Cages = {}
    for key, val in kwargs.items():
      key = key.strip().lower()
      val = val.strip().lower()
      if key.startswith('cage'):
        cage = int(key[4:].strip())
        self.Cages[cage] = _bottles[val]
      
  @classmethod
  def fromCSV(cls, filename, **kwargs):
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

        instance = cls(*byLabel, **row)
        if instance.Name is not None:
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
  def fromMeta(cls, meta, **kwargs):
    bottles = Bottles.fromMeta(meta)
    groups = {}
    partitions = {}
    animals = Animal.fromMeta(meta, _groups=groups, _partitions=partitions)
    phases = cls.fromCSV(os.path.join(meta, cls._filename),
                         _partitions=partitions,
                         _bottles=bottles)
    return phases, animals, groups

MARYSIA_META = 'meta/'

if os.path.exists(MARYSIA_META):
  MARYSIA_ANIMALS = os.path.join(MARYSIA_META, 'animals.csv')
  
  PARTITIONS = {}
  GROUPS = {}
  ANIMALS = set()
  BOTTLES = {}
  LIQUIDS = {}
  SUBSTANCES = {}
  WEIGHT = {}
  
  with open(MARYSIA_ANIMALS, 'rb') as fh:
    for animal in csv.DictReader(fh):
      name = animal.pop('name').strip()

      deceased = None
      if 'deceased' in animal:
        deceased = animal.pop('deceased').strip()
        if deceased == '':
          deceased = None

      ANIMALS.add(name)

      group = animal.pop('group').strip()
      if group not in GROUPS:
        GROUPS[group] = set()

      if deceased is None:
        # not to analyse dead mice
        GROUPS[group].add(name)
        if 'weight' in animal:
          WEIGHT[name] = float(animal.pop('weight').replace(',', '.'))
  
      for k in animal:
        k = k.strip()
        if k.startswith('partition'):
          partition = int(k[9:])
          if partition not in PARTITIONS:
            PARTITIONS[partition] = {}
  
          cage = animal[k].strip()
          if cage == '':
            cage = None
  
          else:
            cage = int(cage)
            if cage not in PARTITIONS[partition]:
              PARTITIONS[partition][cage] = set()
  
            PARTITIONS[partition][cage].add(name)

  MARYSIA_LIQUIDS = os.path.join(MARYSIA_META, 'liquids.csv')
  with open(MARYSIA_LIQUIDS, 'rb') as fh:
    for liquidDesc in csv.DictReader(fh):
      name = liquidDesc.pop('name').strip().lower()

      if name in ('concentration', 'molar mass', 'density'):
        for substance, value in liquidDesc.items():
          substance = substance.strip().lower()
          if substance == 'density' or not value:
            continue

          value = value.strip().lower()

          if substance not in SUBSTANCES:
            SUBSTANCES[substance] = {}

          SUBSTANCES[substance][name] = value if name == 'concentration' else float(value)

      else:
        LIQUIDS[name] = {'name': name}
        for substance, value in liquidDesc.items():
          substance = substance.strip().lower()
          value = value.strip().lower()
          if not value:
            continue

          # density also counts :-D
          LIQUIDS[name][substance] = float(value) if value != 'medium' else 'medium'


  
  MARYSIA_BOTTLES = os.path.join(MARYSIA_META, 'bottles.csv')
  with open(MARYSIA_BOTTLES, 'rb') as fh:
    for bottleSet in csv.DictReader(fh):
      name = bottleSet.pop('name').strip()
      BOTTLES[name] = {}
  
      for k, liquid in bottleSet.items():
        liquid = liquid.strip().lower()
        k = k.strip().lower()
  
        if k.startswith('corner'):
          corner = int(k[6:])
          BOTTLES[name][corner] = LIQUIDS[liquid]
  
  
  MARYSIA_PHASES = os.path.join(MARYSIA_META, 'phases.csv')
  
  PHASES = {}
  
  with open(MARYSIA_PHASES, 'rb') as fh:
    for i, phase in enumerate(csv.DictReader(fh)):
      start, end = convertTime([phase['start'], phase['end']])
  
      pType = phase.pop('type').strip()
      if pType == '':
        pType = None
  
      try:
        iteration = int(phase.pop('iteration'))
  
      except:
        iteration = None
  
      name = phase.pop('name').strip()
  
      if name == '':
        if pType != None and iteration != None:
          name = '%s %d' % (pType, iteration)
  
        else:
          name = 'Phase %d' % i
  
      partition = int(phase.pop('partition'))

      bottles = {}
      for k in phase.keys():
        k = k.strip().lower()
        if k.startswith('cage'):
          bottleSet = phase[k].strip()
          if bottleSet != '':
            cage = int(k[4:])
            bottles[cage] = BOTTLES[bottleSet]
  
  
      phase = {'start': start,
               'end': end,
               'name': name,
               'type': pType,
               'iteration': iteration,
               'bottles': bottles,
               'groups': GROUPS,
               'partition': partition,
               }
      PHASES[name] = phase

  for phase in PHASES.values():
    partition = phase['partition']
    phase['animals'] = PARTITIONS[partition]

