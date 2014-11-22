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
  _key = staticmethod(lambda x: x['name'])
  _filename = None

  @classmethod
  def fromMeta(cls, meta):
    filename = os.path.join(meta, cls._filename)
    return cls.fromCSV(filename)

  @classmethod
  def fromCSV(cls, filename):
    if not os.path.exists(filename):
      return

    result = {}
    with open(filename, 'rb') as fh:
      #return dict((cls._key(row), cls(*map(row.get, cls._labels)))\
      #            for row in csv.DictReader(fh))
      for row in csv.DictReader(fh):
        key = cls._key(row)
        byLabel = map(row.pop, cls._labels)
        result[key] = cls(*byLabel, **row)

    return result


class Substance(MetadataNode):
  _labels = ['name', 'molar mass', 'density']
  _filename = 'substances.csv'
  
  def __init__(self, Name, MolarMass, Density):
    self.Name = unicode(Name).lower()
    self.MolarMass = float(MolarMass) if MolarMass != '' else None
    self.Density = float(Density) if Density != '' else None

  def __repr__(self):
    return str(self)

  def __str__(self):
    return unicode(self).encode('utf-8')

  def __unicode__(self):
    return self.Name


class Component(object):
  def __init__(self, Substance, Amount=None, Unit=None, VolumeConcentration=None, MassFraction=None):
    self.Substance = Substance
    self.Amount = Amount
    self.Unit = unicode(Unit) if Amount is not None else None
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


class Components(object):
  def __init__(self, components, density=None):
    self.__keys = set()

    for substance, amount, unit in components:
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
              Component(substance, amount, unit,
                        VolumeConcentration=volumeConcentration,
                        MassFraction=massFraction))

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

  def __init__(self, Name, Density, substances=None, **components):
    self.Name = unicode(Name).lower()
    self.Density = float(Density) if Density != '' else None

    self.Medium = {}
    tmp = []
    for key, amount in components.items():
      key = key.lower()
      match = self.__parseSubstance.match(key)
      if not match:
        continue

      substance, unit = match.group('substance', 'unit')
      amount = amount.strip().lower()
      if amount == 'medium':
        self.Medium[unicode(substance)] = substances.get(substance, substance) if substances else substance

      else:
        try:
          amount = float(amount)

        except:
          continue

        tmp.append((substances.get(substance, substance) if substances else substance,
                    amount,
                    unit))

    self.Components = Components(tmp, density=self.Density)

  @classmethod
  def fromCSV(cls, filename, substances=None):
    result = {}
    with open(filename, 'rb') as fh:
      #return dict((cls._key(row), cls(*map(row.get, cls._labels)))\
      #            for row in csv.DictReader(fh))
      for row in csv.DictReader(fh):
        key = cls._key(row)
        byLabel = map(row.pop, cls._labels)
        result[key] = cls(*byLabel, substances=substances, **row)

    return result

  @classmethod
  def fromMeta(cls, meta):
    filename = os.path.join(meta, cls._filename)
    return cls.fromCSV(filename, Substance.fromMeta(meta))

  def __repr__(self):
    return str(self)

  def __str__(self):
    return unicode(self).encode('utf-8')

  def __unicode__(self):
    result = self.Name
    if self.Components:
      result += u': ' + unicode(self.Components)

      if self.Medium:
        result += u' in ' + (u', '.join(sorted(map(unicode, self.Medium.values()))))

    else:
      result += (u', '.join(sorted(map(unicode, self.Medium.values()))))

    return result


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

