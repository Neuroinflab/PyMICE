#!/usr/bin/env python
# encoding: utf-8
###############################################################################
#                                                                             #
#    PyMICE library                                                           #
#                                                                             #
#    Copyright (C) 2015 Jakub M. Kowalski, S. Łęski (Laboratory of            #
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
import unittest
import doctest

from datetime import datetime, timedelta
from pytz import utc

import pymice as pm
from pymice._ICData import (ZipLoader, Merger, LogEntry, EnvironmentalConditions,
                            AirHardwareEvent, DoorHardwareEvent, LedHardwareEvent,
                            UnknownHardwareEvent, ICCage, ICCageManager)
import minimock

from TestTools import Mock, MockIntDictManager, MockStrDictManager, BaseTest

if sys.version_info >= (3, 0):
  unicode = str
  basestring = str


def toStrings(seq):
  return [str(x) if x is not None else None for x in seq]

def toUnicodes(seq):
  return [(unicode(x), unicode) if x is not None else None for x in seq]

def floatToStrings(seq, pattern='%.3f'):
  return [pattern % x if x is not None else None for x in seq]


def floatToTimedelta(seq):
  return [timedelta(seconds=x) if x is not None else None for x in seq]



class TestZipLoader(BaseTest):
  def setUp(self):
    self.cageManager = MockIntDictManager()
    self.animalManager = MockStrDictManager()
    self.source = Mock()
    self.loader = ZipLoader(self.source,
                            self.cageManager,
                            self.animalManager)

  def testLoadEmptyVisits(self):
    visits = self.loader.loadVisits({'VisitID': [],
                                    'AnimalTag': [],
                                    'Start': [],
                                    'End': [],
                                    'ModuleName': [],
                                    'Cage': [],
                                    'Corner': [],
                                    'CornerCondition': [],
                                    'PlaceError': [],
                                    'AntennaNumber': [],
                                    'AntennaDuration': [],
                                    'PresenceNumber': [],
                                    'PresenceDuration': [],
                                    'VisitSolution': [],
                                    })
    self.assertEqual(visits, [])

  def testLoadOneVisit(self):
    start = datetime(1970, 1, 1, tzinfo=utc)
    end = start + timedelta(seconds=15)

    visits = self.loader.loadVisits({'VisitID': ['1'],
                                    'AnimalTag': ['10'],
                                    'Start': [start],
                                    'End': [end],
                                    'ModuleName': ['Default'],
                                    'Cage': ['1'],
                                    'Corner': ['2'],
                                    'CornerCondition': ['1'],
                                    'PlaceError': ['0'],
                                    'AntennaNumber': ['1'],
                                    'AntennaDuration': ['1.125'],
                                    'PresenceNumber': ['2'],
                                    'PresenceDuration': ['2.250'],
                                    'VisitSolution': ['0'],
                                    })
    for name, tests in [('Animal', [('10', self.animalManager.Cls),
                                    ]),
                        ('Start', [start]),
                        ('End', [end]),
                        ('Module', [('Default', unicode),
                                   ]),
                        ('Cage', [(1, self.cageManager.Cls),
                                  ]),
                        ('Corner', [(2, self.cageManager.items[1].Cls),
                                    ]),
                        ('CornerCondition', [(1, int)]),
                        ('PlaceError',  [(0, int)]),
                        ('AntennaNumber', [(1, int)]),
                        ('AntennaDuration', [timedelta(seconds=1.125)]),
                        ('PresenceNumber', [(2, int)]),
                        ('PresenceDuration', [timedelta(seconds=2.25)]),
                        ('VisitSolution', [(0, int)]),
                        ('_source', [self.source]),
                        ('_line', [1]),
                        ('Nosepokes', [None]),
                        ]:
      self.checkAttributeSeq(visits, name, tests)

    self.assertEqual(self.animalManager.sequence, [('__getitem__', '10')])
    self.assertTrue(('__getitem__', '1') in self.cageManager.sequence)
    self.assertTrue(('__getitem__', '2') in self.cageManager.items[1].sequence)

  #@unittest.skip('botak')
  def testLoadManyVisitsWithMissingValues(self):
    nVisits = 10
    vNumbers = range(1, nVisits + 1)
    animals = [str(1 + i % 2) for i in vNumbers]
    start = datetime(1970, 1, 1, tzinfo=utc)
    starts = [start + timedelta(seconds=10 * i) for i in vNumbers]
    ends = [None if i == 1 else start + timedelta(seconds=15 + 10 * i) for i in vNumbers]
    modules = [None if i == 2 else str(i) for i in vNumbers]
    cages = [1 + (i % 2) * 4 for i in vNumbers]
    corners = [1 + (i // 2) % 4 for i in vNumbers]
    conditions = [None if i == 3 else 1 - i % 3 for i in vNumbers]
    errors = [None if i == 4 else 1 if c is None else int(c < 0) for i, c in zip(vNumbers, conditions)]
    aNumbers = [None if i == 5 else i % 3 for i in vNumbers]
    aDurations = [None if i == 6 else i % 3 * 0.125 for i in vNumbers]
    pNumbers = [None if i == 7 else i % 4 for i in vNumbers]
    pDurations = [None if i == 8 else i % 4 * 0.125 for i in vNumbers]
    solutions = [None if i == 9 else i % 4 for i in vNumbers]
    nones = [None] * nVisits

    inputCollumns = {'VisitID': toStrings(vNumbers),
                     'AnimalTag': toStrings(animals),
                     'Start': starts,
                     'End': ends,
                     'ModuleName': modules,
                     'Cage': toStrings(cages),
                     'Corner': toStrings(corners),
                     'CornerCondition': toStrings(conditions),
                     'PlaceError': toStrings(errors),
                     'AntennaNumber': toStrings(aNumbers),
                     'AntennaDuration': floatToStrings(aDurations),
                     'PresenceNumber': toStrings(pNumbers),
                     'PresenceDuration': floatToStrings(pDurations),
                     'VisitSolution': toStrings(solutions),
                     }
    outputColumns = {'Animal': toStrings(animals),
                     'Start': starts,
                     'End': ends,
                     'Module': toUnicodes(modules),
                     'Cage': cages,
                     'Corner': corners,
                     'CornerCondition': conditions,
                     'PlaceError': errors,
                     'AntennaNumber': aNumbers,
                     'AntennaDuration': floatToTimedelta(aDurations),
                     'PresenceNumber': pNumbers,
                     'PresenceDuration': floatToTimedelta(pDurations),
                     'VisitSolution': solutions,
                     '_source': [self.source] * nVisits,
                     '_line': vNumbers,
                     'Nosepokes': nones,
                     }
    for descCol in [None,
                    'End',
                    ('ModuleName', 'Module'),
                    'CornerCondition',
                    'PlaceError',
                    'AntennaNumber',
                    'AntennaDuration',
                    'PresenceNumber',
                    'PresenceDuration',
                    'VisitSolution']:
      inCols = dict(inputCollumns)
      outCols = dict(outputColumns)
      if descCol is not None:
        inCol, outCol = (descCol, descCol) if isinstance(descCol, basestring) else descCol
        inCols.pop(inCol)
        outCols.pop(outCol)

      visits = self.loader.loadVisits(inCols)
      for name, tests in outCols.items():
        self.checkAttributeSeq(visits, name, tests)

  def testLoadOneVisitNoNosepokes(self):
    start = datetime(1970, 1, 1, tzinfo=utc)
    visits = self.loader.loadVisits({'VisitID': ['1'],
                                     'AnimalTag': ['10'],
                                     'Start': [start],
                                     'End': [start],
                                     'ModuleName': ['Default'],
                                     'Cage': ['1'],
                                     'Corner': ['2']},
                                    {'VisitID': [],
                                     'Start': [],
                                     'End': [],
                                     'Side': [],
                                     'SideCondition': [],
                                     'SideError': [],
                                     'TimeError': [],
                                     'ConditionError': [],
                                     'LickNumber': [],
                                     'LickContactTime': [],
                                     'LickDuration': [],
                                     'AirState': [],
                                     'DoorState': [],
                                     'LED1State': [],
                                     'LED2State': [],
                                     'LED3State': []
                                     })
    self.assertEqual(visits[0].Nosepokes, ())

  def testLoadOneVisitOneNosepoke(self):
    start = datetime(1970, 1, 1, tzinfo=utc)
    end = start + timedelta(seconds=12)
    visits = self.loader.loadVisits({'VisitID': ['1'],
                                     'AnimalTag': ['10'],
                                     'Start': [start],
                                     'End': [end],
                                     'Cage': ['4'],
                                     'Corner': ['2']},
                                    {'VisitID': ['1'],
                                     'Start': [start],
                                     'End': [end],
                                     'Side': ['4'],
                                     'SideCondition': ['1'],
                                     'SideError': ['0'],
                                     'TimeError': ['1'],
                                     'ConditionError': ['1'],
                                     'LickNumber': ['0'],
                                     'LickContactTime': ['0.500'],
                                     'LickDuration': ['1.5'],
                                     'AirState': ['0'],
                                     'DoorState': ['1'],
                                     'LED1State': ['0'],
                                     'LED2State': ['1'],
                                     'LED3State': ['0']
                                     })
    nosepoke = visits[0].Nosepokes[0]
    self.checkAttributes(nosepoke,
                         [('Start', start),
                          ('End', end),
                          ('Side', 4, self.cageManager.items[4].items[2].Cls),
                          ('SideCondition', 1, int),
                          ('SideError', 0, int),
                          ('TimeError', 1, int),
                          ('ConditionError', 1, int),
                          ('LickNumber', 0, int),
                          ('LickContactTime', timedelta(seconds=0.5)),
                          ('LickDuration', timedelta(seconds=1.5)),
                          ('AirState', 0, int),
                          ('DoorState', 1, int),
                          ('LED1State', 0, int),
                          ('LED2State', 1, int),
                          ('LED3State', 0, int),
                          ('_source', self.source),
                          ('_line', 1)])
    self.assertEqual(self.cageManager.items[4].items[2].sequence, [('__getitem__', '4')])

  def testManyVisitsManyNosepokes(self):
    nVisits = 4
    vIds = range(1, nVisits + 1)
    start = datetime(1970, 1, 1, tzinfo=utc)
    end = start + timedelta(seconds=12)
    corners = [1 + (i - 1) % 2 for i in vIds]
    cages = [1 + 3 * ((i - 1) // 2) for i in vIds]
    inputVColumns = {'VisitID': toStrings(vIds),
                     'AnimalTag': toStrings(vIds),
                     'Start': [start] * nVisits,
                     'End': [end] * nVisits,
                     'Cage': toStrings(cages),
                     'Corner': toStrings(corners)}

    nIds = [i for i in vIds for _ in range(1, i)]
    nNps = len(nIds)
    _lines = range(1, nNps + 1)
    nStarts = [start + timedelta(seconds=2002 - 10 * i) for i in _lines]
    nEnds = [start + timedelta(seconds=2007 - 10 * i) for i in _lines]
    sides = [vId * 2 - i % 2 for i, vId in enumerate(nIds, 1)]
    sideConditions = [i % 3 - 1 for i in _lines]
    sideErrors = [1 if c < 0 else 0 for c in sideConditions]
    timeErrors = [(i + 1) % 3 - 1 for i in _lines]
    conditionErrors = [(i + 2) % 3 - 1 for i in _lines]
    lickNumbers = [i * j for i, j in zip(nIds, _lines)]
    lickContactTimes = [0.125 * i for i in lickNumbers]
    lickDurations = [3. * i for i in lickContactTimes]
    airState = [i % 2 for i in _lines]
    doorState = [1 - i % 2 for i in _lines]
    led1state = [i // 2 % 2 for i in _lines]
    led2state = [1 - i // 2 % 2 for i in _lines]
    led3state = [i // 3 % 2 for i in _lines]
    inputNColumns = {'VisitID': toStrings(nIds),
                     'Start': nStarts,
                     'End': nEnds,
                     'Side': toStrings(sides),
                     'SideCondition': toStrings(sideConditions),
                     'SideError': toStrings(sideErrors),
                     'TimeError': toStrings(timeErrors),
                     'ConditionError': toStrings(conditionErrors),
                     'LickNumber': toStrings(lickNumbers),
                     'LickContactTime': floatToStrings(lickContactTimes),
                     'LickDuration': floatToStrings(lickDurations),
                     'AirState': toStrings(airState),
                     'DoorState': toStrings(doorState),
                     'LED1State': toStrings(led1state),
                     'LED2State': toStrings(led2state),
                     'LED3State': toStrings(led3state),
                     }
    outputNColumns = {'Start': nStarts,
                      'End': nEnds,
                      'Side': sides,
                      'SideCondition': sideConditions,
                      'SideError': sideErrors,
                      'TimeError': timeErrors,
                      'ConditionError': conditionErrors,
                      'LickNumber': lickNumbers,
                      'LickContactTime': floatToTimedelta(lickContactTimes),
                      'LickDuration': floatToTimedelta(lickDurations),
                      'AirState': airState,
                      'DoorState': doorState,
                      'LED1State': led1state,
                      'LED2State': led2state,
                      'LED3State': led3state,
                      '_line': _lines
                      }

    for descCol in [None,
                    'End',
                    'Side',
                    'SideCondition',
                    'SideError',
                    'TimeError',
                    'ConditionError',
                    'LickNumber',
                    'LickContactTime',
                    'LickDuration',
                    'AirState',
                    'DoorState',
                    'LED1State',
                    'LED2State',
                    'LED3State',]:
        inCols = dict(inputNColumns)
        outCols = dict(outputNColumns)
        if descCol is not None:
            inCols.pop(descCol)
            outCols.pop(descCol)

        visits = self.loader.loadVisits(inputVColumns, inCols)
        self.assertEqual([len(v.Nosepokes) for v in visits],
                         [i - 1 for i in vIds])

        nosepokes = [n for v in visits for n in sorted(v.Nosepokes, key=lambda x: x._line)]
        for name, values in outCols.items():
          self.checkAttributeSeq(nosepokes, name, values)

        self.assertEqual([n._line for v in visits for n in v.Nosepokes],
                         [x[2] for x in sorted(zip(nIds, nStarts, _lines))])


  def testLoadEmptyLog(self):
    log = self.loader.loadLog({'DateTime': [],
                               'LogCategory': [],
                               'LogType': [],
                               'Cage': [],
                               'Corner': [],
                               'Side': [],
                               'LogNotes': [],
                               })
    self.assertEqual(log, [])

  def testLoadLog(self):
    nLog = 5
    times = [datetime(1970, 1, 1, i, tzinfo=utc) for i in range(nLog)]
    categories = ['Info', 'Warning', 'Warning', 'Fake', 'Fake']
    types = ['Application', 'Presence', 'Lickometer', 'Fake', 'Fake']
    cages = [None, 2, 3, 1, 1]
    corners = [None, 4, 1, None, 1]
    sides = [None, None, 2, None, 1]
    notes = ['Session is started',
             'Presence signal without antenna registration.',
             'Lickometer is active but nosepoke is inactive',
             'Fake note',
             None]
    log = self.loader.loadLog({'DateTime': times,
                               'LogCategory': categories,
                               'LogType': types,
                               'Cage': toStrings(cages),
                               'Corner': toStrings(corners),
                               'Side': toStrings(sides),
                               'LogNotes': notes,
                               })
    self.assertEqual(len(log), nLog)
    for name, tests in [('DateTime', times),
                        ('Category', toUnicodes(categories)),
                        ('Type', toUnicodes(types)),
                        ('Cage', cages),
                        ('Corner', corners),
                        ('Side', sides),
                        ('Notes', toUnicodes(notes)),
                        ('_source', [self.source] * nLog),
                        ('_line', range(1, nLog + 1)),
                        ]:
      self.checkAttributeSeq(log, name, tests)

    for entry, cage, corner, side in zip(log, cages, corners, sides):
      if cage is not None:
        self.assertIs(entry.Cage, self.cageManager.items[cage])
        if corner is not None:
          self.assertIs(entry.Corner, entry.Cage.items[corner])
          if side is not None:
            self.assertIs(entry.Side, entry.Corner.items[side])

  def testLoadEmptyEnv(self):
    self.assertEqual(self.loader.loadEnv({
                     'DateTime': [],
                     'Temperature': [],
                     'Illumination': [],
                     'Cage': [],
                     }),
                     [])

  def testLoadEnv(self):
    times = [datetime(1970, 1, 1, tzinfo=utc)] * 2
    temperature = [20, 20.5]
    illumination = [255, 0]
    cages = [1, 2]
    envs = self.loader.loadEnv({'DateTime': times,
                                'Temperature': floatToStrings(temperature, '%.1f'),
                                'Illumination': toStrings(illumination),
                                'Cage': toStrings(cages)})
    self.assertEqual(len(envs), 2)
    for name, tests in [('DateTime', times),
                        ('Temperature', temperature),
                        ('Illumination', illumination),
                        ('Cage', cages),
                        ('_source', [self.source] * 2),
                        ('_line', [1, 2])]:
      self.checkAttributeSeq(envs, name, tests)

    for e in envs:
      self.assertIs(e.Cage, self.cageManager.items[e.Cage])


  def testLoadEmptyHw(self):
    self.assertEqual(self.loader.loadHw({
                     'DateTime': [],
                     'Type': [],
                     'Cage': [],
                     'Corner': [],
                     'Side': [],
                     'State': [],
                     }),
                     [])

  def testLoadHw(self):
    n = 4
    times = [datetime(1970, 1, 1, tzinfo=utc)] * n
    types = range(n)
    cages = range(1, n + 1)
    corners = [1 + i % 4 for i in range(n)]
    sides = [None] + [(1 + i % 4) * 2 - i % 2 for i in range(1, n)]
    states = [i % 2 for i in range(n)]
    hwTypes = [AirHardwareEvent, DoorHardwareEvent, LedHardwareEvent] \
              + [UnknownHardwareEvent] * (n - 3)
    hws = self.loader.loadHw({'DateTime': times,
                              'Type': toStrings(types),
                              'Cage': toStrings(cages),
                              'Corner': toStrings(corners),
                              'Side': toStrings(sides),
                              'State': toStrings(states),
                              })
    self.assertEqual(len(hws), n)
    for name, tests in [('DateTime', times),
                        ('Type', types),
                        ('Cage', cages),
                        ('Corner', corners),
                        ('Side', sides),
                        ('State', states),
                        ('_source', [self.source] * n),
                        ('_line', range(1, n + 1))]:
      self.checkAttributeSeq(hws, name, tests)

    for hw, hwType in zip(hws, hwTypes):
      self.assertIsInstance(hw, hwType)

    for hw in hws:
      if hw.Cage is not None:
        self.assertIs(hw.Cage, self.cageManager.items[hw.Cage])
        if hw.Corner is not None:
          self.assertIs(hw.Corner, hw.Cage.items[hw.Corner])
          if hw.Side is not None:
            self.assertIs(hw.Side, hw.Corner.items[hw.Side])


class ICCageTest(unittest.TestCase):
  def setUp(self):
    self.cage = ICCage(42)

  def testFromStr(self):
    self.assertEqual(11, ICCage('11'))

  def testInt(self):
    self.assertEqual(42, self.cage)

  def testCorners(self):
    self.assertRaises(ICCage.NoCornerError, lambda: self.cage[0])
    self.assertRaises(ICCage.NoCornerError, lambda: self.cage[5])

    for i in range(1, 5):
      corner = self.cage[i]
      self.assertEqual(i, corner)
      self.assertIs(corner, self.cage[str(i)])

      self._checkCorner(corner)

      self.assertIs(corner.Cage, self.cage)

  def _checkCorner(self, corner):
    self.assertRaises(corner.NoSideError, lambda: corner[corner * 2 - 2])
    self.assertRaises(corner.NoSideError, lambda: corner[corner * 2 + 1])
    for j, s in enumerate(['left', 'right'], corner * 2 - 1):
      side = corner[j]
      self.assertEqual(str(j), str(side))

      self.assertTrue(j == side)
      self.assertFalse(j != side)
      self.assertTrue(j + 1 != side)
      self.assertFalse(j + 1 == side)

      self.assertIs(side, corner[s])
      self.assertIs(side, corner[str(j)])
      self.assertIs(side, getattr(corner, s.capitalize()))

      self.assertIs(side.Corner, corner)

  def testDel(self):
    corners = [self.cage[i] for i in range(1, 5)]
    sides = [corner[s] for corner in corners for s in ['left', 'right']]
    self.cage._del_()
    for corner in corners:
      self.assertRaises(AttributeError, lambda: corner.Cage)

    for side in sides:
      self.assertRaises(AttributeError, lambda: side.Corner)

  def testReadOnly(self):
    self.assertRaises(AttributeError, lambda: setattr(self.cage, 'Nonexistingattr', None))

    corner = self.cage[1]
    self.assertRaises(AttributeError, lambda: setattr(corner, 'Cage', None))
    self.assertRaises(AttributeError, lambda: setattr(corner, 'Nonexistingattr', None))

    side = corner['left']
    self.assertRaises(AttributeError, lambda: setattr(side, 'Corner', None))
    self.assertRaises(AttributeError, lambda: setattr(side, 'Nonexistingattr', None))


class ICCageManagerTest(unittest.TestCase):
  def setUp(self):
    self.cageManager = ICCageManager()
    self.ICCage = pm._ICData.ICCage

  def tearDown(self):
    pm._ICData.ICCage = self.ICCage

  def testGet(self):
    cages = set()
    def newCage(cage):
      cages.add(cage)
      return minimock.Mock('ICCage(%s)' % cage,
                           returns=cage)
    pm._ICData.ICCage = minimock.Mock('Data.ICCage',
                                   returns_func=newCage)

    cageNumber = 1
    cage = self.cageManager[cageNumber]
    self.assertIs(cage(), cageNumber)
    self.assertTrue(cageNumber in cages)
    self.assertIs(cage, self.cageManager[cageNumber])
    self.assertIs(cage, self.cageManager[str(cageNumber)])

  def testDel(self):
    cages = {}
    delCalled = set()
    def newCage(cage):
      try:
        return cages[cage]

      except KeyError:
        item = minimock.Mock('ICCage(%s)' % cage)
        item._del_.mock_returns_func = lambda: delCalled.add(cage)
        cages[cage] = item
        return item

    pm._ICData.ICCage = minimock.Mock('Data.ICCage')
    pm._ICData.ICCage.mock_returns_func = newCage

    for i in range(1, 10):
      for j in range(1, i + 1):
        self.cageManager[j]

    self.cageManager._del_()
    for cage in cages:
      self.assertTrue(cage in delCalled)

  def testReadOnly(self):
    self.assertRaises(AttributeError, lambda: setattr(self.cageManager, 'Nonexistingattr', None))


class DataTest(unittest.TestCase):
  def testDel(self):
    ICCage = pm._ICData.ICCage

    def getMockCage(n):
      cage = minimock.Mock('ICCage')
      cage._del_ = lambda: cagesDeleted.add(n)
      return cage

    pm._ICData.ICCage = minimock.Mock('ICCage',
                                      returns_func=getMockCage)

    deleted = set()
    cagesDeleted = set()
    toDelete = []
    cagesToDelete = []
    data = pm.Data.Data(CageManager=pm._ICData.ICCageManager) # XXX: ugly test -> split testing of ICCageManager and Data.__del__

    def makeCloneInjector(cage, label):
      toDelete.append(label)
      cagesToDelete.append(cage)
      cloneInjector = minimock.Mock('CloneInjector')
      def cloneReporter(sourceManager, cageManager, *args):
        cageManager[cage]
        clone = minimock.Mock(label)
        clone._del_.mock_returns_func = lambda: deleted.add(label)
        return clone

      cloneInjector.clone.mock_returns_func = cloneReporter
      return cloneInjector

    data.insertVisits([makeCloneInjector(1, 'Visit')])
    data.insertLog([makeCloneInjector(2, 'Log')])
    data.insertEnv([makeCloneInjector(3, 'Env')])
    data.insertHw([makeCloneInjector(4, 'Hw')])
    data.__del__()

    for label in toDelete:
      self.assertIn(label, deleted)

    for cage in cagesToDelete:
      self.assertIn(cage, cagesDeleted)

    pm._ICData.ICCage = ICCage


class MergerTest(unittest.TestCase):
  def setUp(self):
    self.d1 = pm.Data.Data()
    self.d2 = pm.Data.Data()
    self.time1 = datetime(1970, 1, 1, tzinfo=utc)
    self.time2 = datetime(1970, 1, 1, 1, tzinfo=utc)

  def testLogMerge(self):
    self.d1.insertLog([LogEntry(self.time1,
                                u'Test', u'D1',
                                1, 2, 3,
                                u'Note',
                                u'D1', 1)])
    self.d2.insertLog([LogEntry(self.time2,
                                u'Test', u'D2',
                                1, 2, 3,
                                u'Note',
                                u'D2', 1)])
    mm = Merger(self.d1, self.d2, getLog=True)
    self.assertEqual([u'D1', u'D2'],
                     [l.Type for l in mm.getLog(order='DateTime')])

  def testEnvMerge(self):
    self.d1.insertEnv([EnvironmentalConditions(self.time1,
                                               12.5, 255, 1, u'D1', 1)])
    self.d2.insertEnv([EnvironmentalConditions(self.time2,
                                               11.5, 0, 3, u'D2', 1)])
    mm = Merger(self.d1, self.d2, getEnv=True)
    self.assertEqual([12.5, 11.5],
                     [l.Temperature for l in mm.getEnvironment(order='DateTime')])

  def testHwMerge(self):
    self.d1.insertHw([UnknownHardwareEvent(self.time2, 42, 1, 2, 3, 44, u'D1', 1)])
    self.d2.insertHw([AirHardwareEvent(self.time1, 1, 2, 3, 1, u'D2', 1)])
    mm = Merger(self.d1, self.d2, getHw=True)
    self.assertEqual([u'D2', u'D1'],
                     [h._source for h in mm.getHardwareEvents(order='DateTime')])


if __name__ == '__main__':
  testDir = os.path.abspath(os.path.dirname(__file__))
  TEST_GLOBALS = {
    #XXX: ml_l1 - not sure if data format is valid
    'ml_l1': pm.Loader(os.path.join(testDir, 'legacy_data.zip')),
    #'ml_a1': pm.Loader(os.path.join(testDir, 'analyzer_data.txt'), getNpokes=True),
    'ml_icp3': pm.Loader(os.path.join(testDir, 'icp3_data.zip'),
                      getLog=True, getEnv=True),
    'ml_empty': pm.Loader(os.path.join(testDir, 'empty_data.zip')),
    'ml_retagged': pm.Loader(os.path.join(testDir, 'retagged_data.zip')),
  }

  doctest.testmod(pm.Data, extraglobs=TEST_GLOBALS)

  unittest.main()
