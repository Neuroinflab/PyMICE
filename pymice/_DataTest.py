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

import unittest
from datetime import datetime, timedelta
from pytz import utc

from Data import ZipLoader

from _TestTools import Mock, MockIntDictManager, MockCageManager, \
                       MockStrDictManager, BaseTest


def toStrings(seq):
  return [str(x) if x is not None else None for x in seq]


def floatToStrings(seq):
  return ['%.3f' % x if x is not None else None for x in seq]


def floatToTimedelta(seq):
  return [timedelta(seconds=x) if x is not None else None for x in seq]



class TestZipLoader(BaseTest):
  def setUp(self):
    self.cageManager = MockCageManager()
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
                        ('Corner', [(2, self.cageManager.managers[1].Cls),
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

    self.assertEqual(self.animalManager.sequence, [('get', '10')])
    #self.assertEqual(self.cageManager.sequence[0], ('getCageCorner', 1, 2))
    self.assertTrue(('get', 1) in self.cageManager.sequence)
    self.assertTrue(('getManager', 1) in self.cageManager.sequence)
    self.assertTrue(('get', 2) in self.cageManager.managers[1].sequence)

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
    corners = [1 + (i / 2) % 4 for i in vNumbers]
    conditions = [None if i == 3 else 1 - i % 3 for i in vNumbers]
    errors = [None if i == 4 else int(c < 0) for i, c in zip(vNumbers, conditions)]
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
                     'Module': modules,
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
                          ('Side', 4, self.cageManager.managers[4].managers[2].Cls),
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
    self.assertEqual(self.cageManager.managers[4].managers[2].sequence, [('get', 4)])

  def testManyVisitsManyNosepokes(self):
    nVisits = 4
    vIds = range(1, nVisits + 1)
    start = datetime(1970, 1, 1, tzinfo=utc)
    end = start + timedelta(seconds=12)
    corners = [1 + (i - 1) % 2 for i in vIds]
    cages = [1 + 3 * ((i - 1) / 2) for i in vIds]
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
    led1state = [i / 2 % 2 for i in _lines]
    led2state = [1 - i / 2 % 2 for i in _lines]
    led3state = [i / 3 % 2 for i in _lines]
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

if __name__ == '__main__':
  unittest.main()