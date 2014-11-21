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

from ._Loader import convertTime

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

