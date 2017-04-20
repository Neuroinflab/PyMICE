#!/usr/bin/env python
# encoding: utf-8
###############################################################################
#                                                                             #
#    PyMICE library                                                           #
#                                                                             #
#    Copyright (C) 2015-2017 Jakub M. Dzik a.k.a. Kowalski, S. Łęski          #
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

import sys
import os
import unittest

from datetime import datetime, timedelta
from pytz import utc, timezone

import pymice as pm
from pymice._ICData import (ZipLoader_v_IntelliCage_Plus_3, ZipLoader_v_Version1,
                            Merger, LogEntry, EnvironmentalConditions,
                            AirHardwareEvent, DoorHardwareEvent, LedHardwareEvent,
                            UnknownHardwareEvent, ICCage, ICCageManager)
from pymice.Data import Data, IntIdentityManager

import minimock

from ._TestTools import (Mock, MockIntDictManager, MockStrDictManager, BaseTest,
                         isString)

if sys.version_info >= (3, 0):
  unicode = str


def toStrings(seq):
  return [str(x) if x is not None else None for x in seq]

def toUnicodes(seq):
  return [(unicode(x), unicode) if x is not None else None for x in seq]

def floatToStrings(seq, pattern='%.3f'):
  return [pattern % x if x is not None else None for x in seq]


def floatToTimedelta(seq):
  return [timedelta(seconds=x) if x is not None else None for x in seq]



class TestZipLoader_v_IntelliCage_Plus_3(BaseTest):
  loaderClass = ZipLoader_v_IntelliCage_Plus_3

  def setUp(self):
    self.cageManager = MockIntDictManager()
    self.animalManager = MockStrDictManager()
    self.source = Mock()
    self.loader = self.loaderClass(self.source,
                                   self.cageManager,
                                   self.animalManager)

  INPUT_LOAD_ANIMALS = {'AnimalName': ['Minie', 'Mickey', 'Jerry'],
                        'AnimalTag': ['1337', '42', '69'],
                        'Sex': ['Female', 'Male', 'Male'],
                        'GroupName': ['Disney', 'Disney', 'HannaBarbera'],
                        'AnimalNotes': [None, None, 'Likes Tom']}
  OUTPUT_LOAD_ANIMALS = {'Name': [u'Minie', u'Mickey', u'Jerry'],
                         'Tag': [{'1337'}, {'42'}, {'69'}],
                         'Sex': ['Female', 'Male', 'Male'],
                         'Notes': [set(), set(), {'Likes Tom'}]}
  OUTPUT_LOAD_GROUPS = {'Disney': {'Minie', 'Mickey'},
                        'HannaBarbera': {'Jerry'}}

  def testLoadEmptyAnimals(self):
    self.checkMethodWithEmptyData(self.loaderClass.loadAnimals,
                                  self.INPUT_LOAD_ANIMALS)

  def testLoadAnimals(self):
    animals = self.loaderClass.loadAnimals(self.INPUT_LOAD_ANIMALS)
    for name, tests in self.OUTPUT_LOAD_ANIMALS.items():
      self.checkAttributeSeq(animals, name, tests)

  def testLoadEmptyGroups(self):
      self.assertEqual({},
                       self.loaderClass.loadGroups(
                           self.makeEmptyColumns(self.INPUT_LOAD_ANIMALS)))

  def makeEmptyColumns(self, keys):
      return {key: [] for key in keys}

  def testLoadGroups(self):
    groups = self.loaderClass.loadGroups(self.INPUT_LOAD_ANIMALS)
    self.assertEqual(self.OUTPUT_LOAD_GROUPS, groups)

  def testLoadEmptyVisits(self):
    self.checkMethodWithEmptyData(self.loader.loadVisits,
                                  self.INPUT_LOAD_ONE_VISIT)

  INPUT_LOAD_ONE_VISIT = {'VisitID': ['1'],
                          'AnimalTag': ['10'],
                          'Start': [datetime(1970, 1, 1, 0, 0, 0, tzinfo=utc)],
                          'End': [datetime(1970, 1, 1, 0, 0, 15, tzinfo=utc)],
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
                          }
  OUTPUT_LOAD_ONE_VISIT = {'Animal': ['10'],
                           'Start': [datetime(1970, 1, 1, 0, 0, 0, tzinfo=utc)],
                           'End': [datetime(1970, 1, 1, 0, 0, 15, tzinfo=utc)],
                           'Module': [u'Default'],
                           'Cage': [1],
                           'Corner': [2],
                           'CornerCondition': [1],
                           'PlaceError': [0],
                           'AntennaNumber': [1],
                           'AntennaDuration': [timedelta(seconds=1.125)],
                           'PresenceNumber': [2],
                           'PresenceDuration': [timedelta(seconds=2.25)],
                           'VisitSolution': [0],
                           '_line': [1],
                           'Nosepokes': [None],
                           }

  def testLoadOneVisit(self):
    visits = self.loader.loadVisits(self.INPUT_LOAD_ONE_VISIT)

    expected = self.OUTPUT_LOAD_ONE_VISIT
    self.basicNodeCheck(expected, visits)

    for visit in visits:
      self.checkVisitAttributeTypes(visit)

    self.assertEqual(self.animalManager.sequence, [('__getitem__', '10')])
    self.assertTrue(('__getitem__', '1') in self.cageManager.sequence)
    self.assertTrue(('__getitem__', '2') in self.cageManager.items[1].sequence)

  VISIT_INT_ATTRIBUTES = ['CornerCondition', 'PlaceError',
                          'AntennaNumber', 'PresenceNumber',
                          'VisitSolution']
  def checkVisitAttributeTypes(self, visit):
    self.checkAttrsAreInt(visit,
                          *self.VISIT_INT_ATTRIBUTES)
    self.assertIsInstance(visit.Module, unicode, 'Attribute: Module')
    self.assertIsInstance(visit.Animal, self.animalManager.Cls,
                          'Attribute: Animal')
    self.assertIsInstance(visit.Cage, self.cageManager.Cls,
                          'Attribute: Cage')
    self.assertIsInstance(visit.Corner, self.cageManager.items[visit.Cage].Cls,
                          'Attribute: Corner')

    if visit.Nosepokes is not None:
      for nosepoke in visit.Nosepokes:
        self.checkNosepokeAttributeTypes(nosepoke, visit.Cage, visit.Corner)

  def checkNosepokeAttributeTypes(self, nosepoke, cage, corner):
    self.checkAttrsAreInt(nosepoke,
                          'SideCondition', 'SideError', 'TimeError', 'ConditionError',
                          'LickNumber',
                          'AirState', 'DoorState', 'LED1State', 'LED2State', 'LED3State')
    self.assertIsInstance(nosepoke.Side, self.cageManager.items[cage].items[corner].Cls,
                          'Attribute: Side')


  def checkAttrsAreInt(self, obj, *attrs):
    for attr in attrs:
      self.assertIsInstance(getattr(obj, attr), int,
                            'Attribute: {}'.format(attr))


  INPUT_LOAD_MANY_VISITS_WITH_MISSING_VALUES = {
    'VisitID': ['1', '2', '3', '4', '5', '6', '7', '8', '9', '10'],
    'AnimalTag': ['2', '1', '2', '1', '2', '1', '2', '1', '2', '1'],
    'Start': [datetime(1970, 1, 1, 0, 0, 10, tzinfo=utc),
              datetime(1970, 1, 1, 0, 0, 20, tzinfo=utc),
              datetime(1970, 1, 1, 0, 0, 30, tzinfo=utc),
              datetime(1970, 1, 1, 0, 0, 40, tzinfo=utc),
              datetime(1970, 1, 1, 0, 0, 50, tzinfo=utc),
              datetime(1970, 1, 1, 0, 1, 0, tzinfo=utc),
              datetime(1970, 1, 1, 0, 1, 10, tzinfo=utc),
              datetime(1970, 1, 1, 0, 1, 20, tzinfo=utc),
              datetime(1970, 1, 1, 0, 1, 30, tzinfo=utc),
              datetime(1970, 1, 1, 0, 1, 40, tzinfo=utc)],
    'End': [None,
            datetime(1970, 1, 1, 0, 0, 35, tzinfo=utc),
            datetime(1970, 1, 1, 0, 0, 45, tzinfo=utc),
            datetime(1970, 1, 1, 0, 0, 55, tzinfo=utc),
            datetime(1970, 1, 1, 0, 1, 5, tzinfo=utc),
            datetime(1970, 1, 1, 0, 1, 15, tzinfo=utc),
            datetime(1970, 1, 1, 0, 1, 25, tzinfo=utc),
            datetime(1970, 1, 1, 0, 1, 35, tzinfo=utc),
            datetime(1970, 1, 1, 0, 1, 45, tzinfo=utc),
            datetime(1970, 1, 1, 0, 1, 55, tzinfo=utc)],
    'ModuleName': ['1', None, '3', '4', '5', '6', '7', '8', '9', '10'],
    'Cage': ['5', '1', '5', '1', '5', '1', '5', '1', '5', '1'],
    'Corner': ['1', '2', '2', '3', '3', '4', '4', '1', '1', '2'],
    'CornerCondition': ['0', '-1', None, '0', '-1', '1', '0', '-1', '1', '0'],
    'PlaceError': ['0', '1', '1', None, '1', '0', '0', '1', '0', '0'],
    'AntennaNumber': ['1', '2', '0', '1', None, '0', '1', '2', '0', '1'],
    'AntennaDuration': ['0.125', '0.25', '0', '0.125', '0.250', None, '0.125', '0.25', '0.000', '0.125'],
    'PresenceNumber': ['1', '2', '3', '0', '1', '2', None, '0', '1', '2'],
    'PresenceDuration': ['0.125', '0.25', '0.375', '0', '0.125', '0.250', '0.375', None, '0.125', '0.250'],
    'VisitSolution': ['1', '2', '3', '0', '1', '2', '3', '0', None, '2'],
  }
  OUTPUT_LOAD_MANY_VISITS_WITH_MISSING_VALUES = {
    'Animal': ['2', '1', '2', '1', '2', '1', '2', '1', '2', '1'],
    'Start': [datetime(1970, 1, 1, 0, 0, 10, tzinfo=utc),
              datetime(1970, 1, 1, 0, 0, 20, tzinfo=utc),
              datetime(1970, 1, 1, 0, 0, 30, tzinfo=utc),
              datetime(1970, 1, 1, 0, 0, 40, tzinfo=utc),
              datetime(1970, 1, 1, 0, 0, 50, tzinfo=utc),
              datetime(1970, 1, 1, 0, 1, 0, tzinfo=utc),
              datetime(1970, 1, 1, 0, 1, 10, tzinfo=utc),
              datetime(1970, 1, 1, 0, 1, 20, tzinfo=utc),
              datetime(1970, 1, 1, 0, 1, 30, tzinfo=utc),
              datetime(1970, 1, 1, 0, 1, 40, tzinfo=utc)],
    'End': [None,
            datetime(1970, 1, 1, 0, 0, 35, tzinfo=utc),
            datetime(1970, 1, 1, 0, 0, 45, tzinfo=utc),
            datetime(1970, 1, 1, 0, 0, 55, tzinfo=utc),
            datetime(1970, 1, 1, 0, 1, 5, tzinfo=utc),
            datetime(1970, 1, 1, 0, 1, 15, tzinfo=utc),
            datetime(1970, 1, 1, 0, 1, 25, tzinfo=utc),
            datetime(1970, 1, 1, 0, 1, 35, tzinfo=utc),
            datetime(1970, 1, 1, 0, 1, 45, tzinfo=utc),
            datetime(1970, 1, 1, 0, 1, 55, tzinfo=utc)],
    'Module': [u'1', None, u'3', u'4', u'5', u'6', u'7', u'8', u'9', u'10'],
    'Cage': [5, 1, 5, 1, 5, 1, 5, 1, 5, 1],
    'Corner': [1, 2, 2, 3, 3, 4, 4, 1, 1, 2],
    'CornerCondition': [0, -1, None, 0, -1, 1, 0, -1, 1, 0],
    'PlaceError': [0, 1, 1, None, 1, 0, 0, 1, 0, 0],
    'AntennaNumber': [1, 2, 0, 1, None, 0, 1, 2, 0, 1],
    'AntennaDuration': floatToTimedelta([0.125, 0.25, 0.0, 0.125, 0.25, None, 0.125, 0.25, 0.0, 0.125]),
    'PresenceNumber': [1, 2, 3, 0, 1, 2, None, 0, 1, 2],
    'PresenceDuration': floatToTimedelta([0.125, 0.25, 0.375, 0.0, 0.125, 0.250, 0.375, None, 0.125, 0.250]),
    'VisitSolution': [1, 2, 3, 0, 1, 2, 3, 0, None, 2],
    '_line': [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
    'Nosepokes': [None, None, None, None, None, None, None, None, None, None]
  }
  MISSING_FIELDS_LOAD_MANY_VISITS_WITH_MISSING_VALUES = [None,
                                                         'End',
                                                         ('ModuleName', 'Module'),
                                                         'CornerCondition',
                                                         'PlaceError',
                                                         'AntennaNumber',
                                                         'AntennaDuration',
                                                         'PresenceNumber',
                                                         'PresenceDuration',
                                                         'VisitSolution']
  def testLoadManyVisitsWithMissingValues(self):
    for descCol in self.MISSING_FIELDS_LOAD_MANY_VISITS_WITH_MISSING_VALUES:
      inCols = dict(self.INPUT_LOAD_MANY_VISITS_WITH_MISSING_VALUES)
      outCols = dict(self.OUTPUT_LOAD_MANY_VISITS_WITH_MISSING_VALUES)
      if descCol is not None:
        inCol, outCol = (descCol, descCol) if isString(descCol) else descCol
        inCols.pop(inCol)
        outCols.pop(outCol)

      visits = self.loader.loadVisits(inCols)
      self.basicNodeCheck(outCols, visits)

  def testLoadOneVisitNoNosepokes(self):
    visits = self.loader.loadVisits(self.INPUT_LOAD_ONE_VISIT,
                                    {key: [] for key in self.INPUT_LOAD_ONE_NOSEPOKE})
    self.assertEqual(visits[0].Nosepokes, ())

  INPUT_LOAD_ONE_NOSEPOKE = {'VisitID': ['1'],
                             'Start': [datetime(1970, 1, 1, 0, 0, 0, tzinfo=utc)],
                             'End': [datetime(1970, 1, 1, 0, 0, 12, tzinfo=utc)],
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
                             }
  OUTPUT_LOAD_ONE_NOSEPOKE = {'Start': [datetime(1970, 1, 1, 0, 0, 0, tzinfo=utc)],
                              'End': [datetime(1970, 1, 1, 0, 0, 12, tzinfo=utc)],
                              'Side': [4],
                              'SideCondition': [1],
                              'SideError': [0],
                              'TimeError': [1],
                              'ConditionError': [1],
                              'LickNumber': [0],
                              'LickContactTime': [timedelta(seconds=0.5)],
                              'LickDuration': [timedelta(seconds=1.5)],
                              'AirState': [0],
                              'DoorState': [1],
                              'LED1State': [0],
                              'LED2State': [1],
                              'LED3State': [0],
                              '_line': [1],
                              }

  def testLoadOneVisitOneNosepoke(self):
    visits = self.loader.loadVisits(self.INPUT_LOAD_ONE_VISIT,
                                    self.INPUT_LOAD_ONE_NOSEPOKE)
    visit = visits[0]
    self.basicNodeCheck(self.OUTPUT_LOAD_ONE_NOSEPOKE, visit.Nosepokes)
    self.checkNosepokeAttributeTypes(visit.Nosepokes[0], 1, 2)
    self.assertEqual(self.cageManager.items[1].items[2].sequence, [('__getitem__', '4')])


  INPUT_LOAD_MANY_VISITS_MANY_NOSEPOKES = {
    'Visits': {'VisitID': ['1', '2', '3', '4'],
               'AnimalTag': ['1', '2', '3', '4'],
               'Start': [datetime(1970, 1, 1, 0, 0, 0, tzinfo=utc),
                         datetime(1970, 1, 1, 0, 0, 0, tzinfo=utc),
                         datetime(1970, 1, 1, 0, 0, 0, tzinfo=utc),
                         datetime(1970, 1, 1, 0, 0, 0, tzinfo=utc),
                         ],
               'End': [datetime(1970, 1, 1, 0, 0, 12, tzinfo=utc),
                       datetime(1970, 1, 1, 0, 0, 12, tzinfo=utc),
                       datetime(1970, 1, 1, 0, 0, 12, tzinfo=utc),
                       datetime(1970, 1, 1, 0, 0, 12, tzinfo=utc),
                       ],
               'Cage': ['1', '1', '4', '4'],
               'Corner': ['1', '2', '1', '2']},
    'Nosepokes': {'VisitID': ['2', '3', '3', '4', '4', '4'],
                  'Start': [datetime(1970, 1, 1, 0, 33, 12, tzinfo=utc),
                            datetime(1970, 1, 1, 0, 33, 2, tzinfo=utc),
                            datetime(1970, 1, 1, 0, 32, 52, tzinfo=utc),
                            datetime(1970, 1, 1, 0, 32, 42, tzinfo=utc),
                            datetime(1970, 1, 1, 0, 32, 32, tzinfo=utc),
                            datetime(1970, 1, 1, 0, 32, 22, tzinfo=utc)],
                     'End': [datetime(1970, 1, 1, 0, 33, 17, tzinfo=utc),
                            datetime(1970, 1, 1, 0, 33, 7, tzinfo=utc),
                            datetime(1970, 1, 1, 0, 32, 57, tzinfo=utc),
                            datetime(1970, 1, 1, 0, 32, 47, tzinfo=utc),
                            datetime(1970, 1, 1, 0, 32, 37, tzinfo=utc),
                            datetime(1970, 1, 1, 0, 32, 27, tzinfo=utc)],
                     'Side': ['3', '6', '5', '8', '7', '8'],
                     'SideCondition': ['0', '1', '-1', '0', '1', '-1'],
                     'SideError': ['0', '0', '1', '0', '0', '1'],
                     'TimeError': ['1', '-1', '0', '1', '-1', '0'],
                     'ConditionError': ['-1', '0', '1', '-1', '0', '1'],
                     'LickNumber': ['2', '6', '9', '16', '20', '24'],
                     'LickContactTime': ['0.25', '0.75', '1.125', '2.0', '2.5', '3.0'],
                     'LickDuration': ['0.75', '2.25', '3.375', '6.0', '7.5', '9.0'],
                     'AirState': ['1', '0', '1', '0', '1', '0'],
                     'DoorState': ['0', '1', '0', '1', '0', '1'],
                     'LED1State': ['0', '1', '1', '0', '0', '1'],
                     'LED2State': ['1', '0', '0', '1', '1', '0'],
                     'LED3State': ['0', '0', '1', '1', '1', '0'],
                     }
  }
  OUTPUT_LOAD_MANY_VISITS_MANY_NOSEPOKES = {
    'Nosepokes':
        {
          'Start': [datetime(1970, 1, 1, 0, 33, 12, tzinfo=utc),
                    datetime(1970, 1, 1, 0, 32, 52, tzinfo=utc),
                    datetime(1970, 1, 1, 0, 33, 2, tzinfo=utc),
                    datetime(1970, 1, 1, 0, 32, 22, tzinfo=utc),
                    datetime(1970, 1, 1, 0, 32, 32, tzinfo=utc),
                    datetime(1970, 1, 1, 0, 32, 42, tzinfo=utc)],
          'End': [datetime(1970, 1, 1, 0, 33, 17, tzinfo=utc),
                  datetime(1970, 1, 1, 0, 32, 57, tzinfo=utc),
                  datetime(1970, 1, 1, 0, 33, 7, tzinfo=utc),
                  datetime(1970, 1, 1, 0, 32, 27, tzinfo=utc),
                  datetime(1970, 1, 1, 0, 32, 37, tzinfo=utc),
                  datetime(1970, 1, 1, 0, 32, 47, tzinfo=utc)],
          'Side': [3, 5, 6, 8, 7, 8],
          'SideCondition': [0, -1, 1, -1, 1, 0],
          'SideError': [0, 1, 0, 1, 0, 0],
          'TimeError': [1, 0, -1, 0, -1, 1],
          'ConditionError': [-1, 1, 0, 1, 0, -1],
          'LickNumber': [2, 9, 6, 24, 20, 16],
          'LickContactTime': floatToTimedelta([0.25, 1.125, 0.75, 3.0, 2.5, 2.0])  ,
          'LickDuration': floatToTimedelta([0.75, 3.375, 2.25, 9.0, 7.5, 6.0]),
          'AirState': [1, 1, 0, 0, 1, 0],
          'DoorState': [0, 0, 1, 1, 0, 1],
          'LED1State': [0, 1, 1, 1, 0, 0],
          'LED2State': [1, 0, 0, 0, 1, 1],
          'LED3State': [0, 1, 0, 0, 1, 1],
          '_line': [1, 3, 2, 6, 5, 4]
        },
    'NosepokeLen': [0, 1, 2, 3],
  }
  MISSING_FIELDS_LOAD_MANY_VISITS_MANY_NOSEPOKES = [None,
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
                                                    'LED3State',]
  def testManyVisitsManyNosepokes(self):
    inputVColumns = self.INPUT_LOAD_MANY_VISITS_MANY_NOSEPOKES['Visits']

    for descCol in self.MISSING_FIELDS_LOAD_MANY_VISITS_MANY_NOSEPOKES:
      inCols = dict(self.INPUT_LOAD_MANY_VISITS_MANY_NOSEPOKES['Nosepokes'])
      outCols = dict(self.OUTPUT_LOAD_MANY_VISITS_MANY_NOSEPOKES['Nosepokes'])
      if descCol is not None:
        if isinstance(descCol, str):
          inCol, outCol = descCol, descCol
        else:
          inCol, outCol = descCol
        inCols.pop(inCol)
        outCols.pop(outCol)

      visits = self.loader.loadVisits(inputVColumns, inCols)
      self.assertEqual([len(v.Nosepokes) for v in visits],
                       self.OUTPUT_LOAD_MANY_VISITS_MANY_NOSEPOKES['NosepokeLen'])

      nosepokes = [n for v in visits for n in v.Nosepokes]
      self.basicNodeCheck(outCols, nosepokes)

      # self.assertEqual([n._line for v in visits for n in v.Nosepokes],
      #                  self.OUTPUT_LOAD_MANY_VISITS_MANY_NOSEPOKES['NosepokeOrder'])


  def testLoadEmptyLog(self):
    self.checkMethodWithEmptyData(self.loader.loadLog,
                                  self.INPUT_LOAD_LOG)

  INPUT_LOAD_LOG = {'DateTime': [datetime(1970, 1, 1, 0, tzinfo=utc),
                                 datetime(1970, 1, 1, 1, tzinfo=utc),
                                 datetime(1970, 1, 1, 2, tzinfo=utc),
                                 datetime(1970, 1, 1, 3, tzinfo=utc),
                                 datetime(1970, 1, 1, 4, tzinfo=utc)],
                    'LogCategory': ['Info', 'Warning', 'Warning', 'Fake', 'Fake'],
                    'LogType': ['Application', 'Presence', 'Lickometer', 'Fake', 'Fake'],
                    'Cage': [None, '2', '3', '1', '1'],
                    'Corner': [None, '4', '1', None, '1'],
                    'Side': [None, None, '2', None, '1'],
                    'LogNotes': ['Session is started',
                                 'Presence signal without antenna registration.',
                                 'Lickometer is active but nosepoke is inactive',
                                 'Fake note',
                                 None],
                     }
  OUTPUT_LOAD_LOG = {'DateTime': [datetime(1970, 1, 1, 0, tzinfo=utc),
                                 datetime(1970, 1, 1, 1, tzinfo=utc),
                                 datetime(1970, 1, 1, 2, tzinfo=utc),
                                 datetime(1970, 1, 1, 3, tzinfo=utc),
                                 datetime(1970, 1, 1, 4, tzinfo=utc)],
                     'Category': [u'Info', u'Warning', u'Warning', u'Fake', u'Fake'],
                     'Type': [u'Application', u'Presence', u'Lickometer', u'Fake', u'Fake'],
                     'Cage': [None, 2, 3, 1, 1],
                     'Corner': [None, 4, 1, None, 1],
                     'Side': [None, None, 2, None, 1],
                     'Notes': [u'Session is started',
                               u'Presence signal without antenna registration.',
                               u'Lickometer is active but nosepoke is inactive',
                               u'Fake note',
                               None],
                     '_line': [1, 2, 3, 4, 5],
                     }

  def testLoadLog(self):
    log = self.loader.loadLog(self.INPUT_LOAD_LOG)

    self.basicNodeCheck(self.OUTPUT_LOAD_LOG, log)

    for entry, cage, corner, side in zip(log,
                                         self.OUTPUT_LOAD_LOG['Cage'],
                                         self.OUTPUT_LOAD_LOG['Corner'],
                                         self.OUTPUT_LOAD_LOG['Side']):
      if cage is not None:
        self.assertIs(entry.Cage, self.cageManager.items[cage])
        if corner is not None:
          self.assertIs(entry.Corner, entry.Cage.items[corner])
          if side is not None:
            self.assertIs(entry.Side, entry.Corner.items[side])

  def testLoadEmptyEnv(self):
    self.checkMethodWithEmptyData(self.loader.loadEnv,
                                  self.INPUT_LOAD_ENV)

  def checkMethodWithEmptyData(self, method, keys):
    self.assertEqual([],
                     method(self.makeEmptyColumns(keys)))

  INPUT_LOAD_ENV = {
    'DateTime': [datetime(1970, 1, 1, tzinfo=utc),
                 datetime(1970, 1, 1, tzinfo=utc)],
    'Temperature': ['20.0', '20.5'],
    'Illumination': ['255', '0'],
    'Cage': ['1', '2'],
    }

  OUTPUT_LOAD_ENV = {
    'DateTime': [datetime(1970, 1, 1, tzinfo=utc),
                 datetime(1970, 1, 1, tzinfo=utc)],
    'Temperature': [20.0, 20.5],
    'Illumination': [255, 0],
    'Cage': [1, 2],
    '_line': [1, 2],
    }

  def testLoadEnv(self):
    for e in self._testLoadEnv():
      self.assertIs(e.Cage, self.cageManager.items[e.Cage])

  def _testLoadEnv(self):
    envs = self.loader.loadEnv(self.INPUT_LOAD_ENV)

    self.basicNodeCheck(self.OUTPUT_LOAD_ENV, envs)

    return envs

  def testLoadEmptyHw(self):
    self.checkMethodWithEmptyData(self.loader.loadHw,
                                  self.INPUT_LOAD_HW)

  INPUT_LOAD_HW = {
    'DateTime': [datetime(1970, 1, 1, tzinfo=utc),
                 datetime(1970, 1, 1, tzinfo=utc),
                 datetime(1970, 1, 1, tzinfo=utc),
                 datetime(1970, 1, 1, tzinfo=utc)],
    'HardwareType': ['0', '1', '2', '3'],
    'Cage': ['1', '2', '3', '4'],
    'Corner': ['1', '2', '3', '4'],
    'Side': [None, '3', '6', '7'],
    'State': ['0', '1', '0', '1'],
    }
  OUTPUT_LOAD_HW = {
    'DateTime': [datetime(1970, 1, 1, tzinfo=utc),
                 datetime(1970, 1, 1, tzinfo=utc),
                 datetime(1970, 1, 1, tzinfo=utc),
                 datetime(1970, 1, 1, tzinfo=utc)],
    'Type': [0, 1, 2, 3],
    'Cage': [1, 2, 3, 4],
    'Corner': [1, 2, 3, 4],
    'Side': [None, 3, 6, 7],
    'State': [0, 1, 0, 1],
    '_line': [1, 2, 3, 4]
    }
  OUTPUT_LOAD_HW_TYPE = [AirHardwareEvent,
                         DoorHardwareEvent,
                         LedHardwareEvent,
                         UnknownHardwareEvent]

  def testLoadHw(self):
    hws = self.loader.loadHw(self.INPUT_LOAD_HW)

    expected = self.OUTPUT_LOAD_HW
    self.basicNodeCheck(expected, hws)

    for hw, hwType in zip(hws, self.OUTPUT_LOAD_HW_TYPE):
        self.assertIsInstance(hw, hwType)

    for hw in hws:
      if hw.Cage is not None:
        self.assertIs(hw.Cage, self.cageManager.items[hw.Cage])
        if hw.Corner is not None:
          self.assertIs(hw.Corner, hw.Cage.items[hw.Corner])
          if hw.Side is not None:
            self.assertIs(hw.Side, hw.Corner.items[hw.Side])

  def basicNodeCheck(self, expected, nodes):
    self.checkAttributeSeq(nodes, '_source', [self.source] * len(expected['_line']))
    for name, tests in expected.items():
      self.checkAttributeSeq(nodes, name, tests)


class TestZipLoader_v_Version1(TestZipLoader_v_IntelliCage_Plus_3):
  loaderClass = ZipLoader_v_Version1

  INPUT_LOAD_ANIMALS = {'Name': ['Minie', 'Mickey', 'Jerry'],
                        'Tag': ['1337', '42', '69'],
                        'Sex': ['Female', 'Male', 'Male'],
                        'Group': ['Disney', 'Disney', 'HannaBarbera'],
                        'Notes': [None, None, 'Likes Tom']}

  INPUT_LOAD_HW = {
    'DateTime': [datetime(1970, 1, 1, tzinfo=utc),
                 datetime(1970, 1, 1, tzinfo=utc),
                 datetime(1970, 1, 1, tzinfo=utc),
                 datetime(1970, 1, 1, tzinfo=utc)],
    'Type': ['0', '1', '2', '3'],
    'Cage': ['0', '1', '2', '3'],
    'Corner': ['0', '1', '2', '3'],
    'Side': [None, '2', '5', '6'],
    'State': ['0', '1', '0', '1'],
    }

  INPUT_LOAD_ENV = {
    'DateTime': [datetime(1970, 1, 1, tzinfo=utc),
                 datetime(1970, 1, 1, tzinfo=utc)],
    'Temperature': ['20.0', '20.5'],
    'Illumination': ['255', '0'],
    }

  OUTPUT_LOAD_ENV = {
    'DateTime': [datetime(1970, 1, 1, tzinfo=utc),
                 datetime(1970, 1, 1, tzinfo=utc)],
    'Temperature': [20.0, 20.5],
    'Illumination': [255, 0],
    'Cage': [None, None],
    '_line': [1, 2],
    }

  def testLoadEnv(self):
    for e in self._testLoadEnv():
      self.assertIs(e.Cage, None)

  INPUT_LOAD_LOG = {'DateTime': [datetime(1970, 1, 1, 0, tzinfo=utc),
                                 datetime(1970, 1, 1, 1, tzinfo=utc),
                                 datetime(1970, 1, 1, 2, tzinfo=utc),
                                 datetime(1970, 1, 1, 3, tzinfo=utc),
                                 datetime(1970, 1, 1, 4, tzinfo=utc)],
                    'Category': ['Info', 'Warning', 'Warning', 'Fake', 'Fake'],
                    'Type': ['Application', 'Presence', 'Lickometer', 'Fake', 'Fake'],
                    'Cage': [None, '1', '2', '0', '0'],
                    'Corner': [None, '3', '0', None, '0'],
                    'Side': [None, None, '1', None, '0'],
                    'Notes': ['Session is started',
                              'Presence signal without antenna registration.',
                              'Lickometer is active but nosepoke is inactive',
                              'Fake note',
                              None],
                     }

  VISIT_INT_ATTRIBUTES = ['CornerCondition', 'PlaceError',
                          'AntennaNumber', 'PresenceNumber',]

  INPUT_LOAD_ONE_VISIT = {'ID': ['1'],
                          'Animal': ['10'],
                          'Start': [datetime(1970, 1, 1, 0, 0, 0, tzinfo=utc)],
                          'End': [datetime(1970, 1, 1, 0, 0, 15, tzinfo=utc)],
                          'ModuleName': ['Default'],
                          'Cage': ['1'],
                          'Corner': ['2'],
                          'CornerCondition': ['1'],
                          'PlaceError': ['0'],
                          'AntennaNumber': ['1'],
                          'AntennaDuration': ['1.125'],
                          'PresenceNumber': ['2'],
                          'PresenceDuration': ['2.250']
                          }
  OUTPUT_LOAD_ONE_VISIT = {'Animal': ['10'],
                           'Start': [datetime(1970, 1, 1, 0, 0, 0, tzinfo=utc)],
                           'End': [datetime(1970, 1, 1, 0, 0, 15, tzinfo=utc)],
                           'Module': [u'Default'],
                           'Cage': [1],
                           'Corner': [2],
                           'CornerCondition': [1],
                           'PlaceError': [0],
                           'AntennaNumber': [1],
                           'AntennaDuration': [timedelta(seconds=1.125)],
                           'PresenceNumber': [2],
                           'PresenceDuration': [timedelta(seconds=2.25)],
                           'VisitSolution': [None],
                           '_line': [1],
                           'Nosepokes': [None],
                           }

  INPUT_LOAD_MANY_VISITS_WITH_MISSING_VALUES = {
    'ID': ['1', '2', '3', '4', '5', '6', '7', '8', '9', '10'],
    'Animal': ['2', '1', '2', '1', '2', '1', '2', '1', '2', '1'],
    'Start': [datetime(1970, 1, 1, 0, 0, 10, tzinfo=utc),
              datetime(1970, 1, 1, 0, 0, 20, tzinfo=utc),
              datetime(1970, 1, 1, 0, 0, 30, tzinfo=utc),
              datetime(1970, 1, 1, 0, 0, 40, tzinfo=utc),
              datetime(1970, 1, 1, 0, 0, 50, tzinfo=utc),
              datetime(1970, 1, 1, 0, 1, 0, tzinfo=utc),
              datetime(1970, 1, 1, 0, 1, 10, tzinfo=utc),
              datetime(1970, 1, 1, 0, 1, 20, tzinfo=utc),
              datetime(1970, 1, 1, 0, 1, 30, tzinfo=utc),
              datetime(1970, 1, 1, 0, 1, 40, tzinfo=utc)],
    'End': [None,
            datetime(1970, 1, 1, 0, 0, 35, tzinfo=utc),
            datetime(1970, 1, 1, 0, 0, 45, tzinfo=utc),
            datetime(1970, 1, 1, 0, 0, 55, tzinfo=utc),
            datetime(1970, 1, 1, 0, 1, 5, tzinfo=utc),
            datetime(1970, 1, 1, 0, 1, 15, tzinfo=utc),
            datetime(1970, 1, 1, 0, 1, 25, tzinfo=utc),
            datetime(1970, 1, 1, 0, 1, 35, tzinfo=utc),
            datetime(1970, 1, 1, 0, 1, 45, tzinfo=utc),
            datetime(1970, 1, 1, 0, 1, 55, tzinfo=utc)],
    'ModuleName': ['1', None, '3', '4', '5', '6', '7', '8', '9', '10'],
    'Cage': ['5', '1', '5', '1', '5', '1', '5', '1', '5', '1'],
    'Corner': ['1', '2', '2', '3', '3', '4', '4', '1', '1', '2'],
    'CornerCondition': ['0', '-1', None, '0', '-1', '1', '0', '-1', '1', '0'],
    'PlaceError': ['0', '1', '1', None, '1', '0', '0', '1', '0', '0'],
    'AntennaNumber': ['1', '2', '0', '1', None, '0', '1', '2', '0', '1'],
    'AntennaDuration': ['0.125', '0.25', '0', '0.125', '0.250', None, '0.125', '0.25', '0.000', '0.125'],
    'PresenceNumber': ['1', '2', '3', '0', '1', '2', None, '0', '1', '2'],
    'PresenceDuration': ['0.125', '0.25', '0.375', '0', '0.125', '0.250', '0.375', None, '0.125', '0.250'],
  }
  OUTPUT_LOAD_MANY_VISITS_WITH_MISSING_VALUES = {
    'Animal': ['2', '1', '2', '1', '2', '1', '2', '1', '2', '1'],
    'Start': [datetime(1970, 1, 1, 0, 0, 10, tzinfo=utc),
              datetime(1970, 1, 1, 0, 0, 20, tzinfo=utc),
              datetime(1970, 1, 1, 0, 0, 30, tzinfo=utc),
              datetime(1970, 1, 1, 0, 0, 40, tzinfo=utc),
              datetime(1970, 1, 1, 0, 0, 50, tzinfo=utc),
              datetime(1970, 1, 1, 0, 1, 0, tzinfo=utc),
              datetime(1970, 1, 1, 0, 1, 10, tzinfo=utc),
              datetime(1970, 1, 1, 0, 1, 20, tzinfo=utc),
              datetime(1970, 1, 1, 0, 1, 30, tzinfo=utc),
              datetime(1970, 1, 1, 0, 1, 40, tzinfo=utc)],
    'End': [None,
            datetime(1970, 1, 1, 0, 0, 35, tzinfo=utc),
            datetime(1970, 1, 1, 0, 0, 45, tzinfo=utc),
            datetime(1970, 1, 1, 0, 0, 55, tzinfo=utc),
            datetime(1970, 1, 1, 0, 1, 5, tzinfo=utc),
            datetime(1970, 1, 1, 0, 1, 15, tzinfo=utc),
            datetime(1970, 1, 1, 0, 1, 25, tzinfo=utc),
            datetime(1970, 1, 1, 0, 1, 35, tzinfo=utc),
            datetime(1970, 1, 1, 0, 1, 45, tzinfo=utc),
            datetime(1970, 1, 1, 0, 1, 55, tzinfo=utc)],
    'Module': [u'1', None, u'3', u'4', u'5', u'6', u'7', u'8', u'9', u'10'],
    'Cage': [5, 1, 5, 1, 5, 1, 5, 1, 5, 1],
    'Corner': [1, 2, 2, 3, 3, 4, 4, 1, 1, 2],
    'CornerCondition': [0, -1, None, 0, -1, 1, 0, -1, 1, 0],
    'PlaceError': [0, 1, 1, None, 1, 0, 0, 1, 0, 0],
    'AntennaNumber': [1, 2, 0, 1, None, 0, 1, 2, 0, 1],
    'AntennaDuration': floatToTimedelta([0.125, 0.25, 0.0, 0.125, 0.25, None, 0.125, 0.25, 0.0, 0.125]),
    'PresenceNumber': [1, 2, 3, 0, 1, 2, None, 0, 1, 2],
    'PresenceDuration': floatToTimedelta([0.125, 0.25, 0.375, 0.0, 0.125, 0.250, 0.375, None, 0.125, 0.250]),
    'VisitSolution': [None, None, None, None, None, None, None, None, None, None],
    '_line': [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
    'Nosepokes': [None, None, None, None, None, None, None, None, None, None]
  }
  MISSING_FIELDS_LOAD_MANY_VISITS_WITH_MISSING_VALUES = [None,
                                                         'End',
                                                         ('ModuleName', 'Module'),
                                                         'CornerCondition',
                                                         'PlaceError',
                                                         'AntennaNumber',
                                                         'AntennaDuration',
                                                         'PresenceNumber',
                                                         'PresenceDuration']

  INPUT_LOAD_ONE_NOSEPOKE = {'VisitID': ['1'],
                             'Start': [datetime(1970, 1, 1, 0, 0, 0, tzinfo=utc)],
                             'End': [datetime(1970, 1, 1, 0, 0, 12, tzinfo=utc)],
                             'Side': ['4'],
                             'SideCondition': ['1'],
                             'SideError': ['0'],
                             'TimeError': ['1'],
                             'ConditionError': ['1'],
                             'LicksNumber': ['0'],
                             'LicksDuration': ['1.5'],
                             'AirState': ['0'],
                             'DoorState': ['1'],
                             'LED1State': ['0'],
                             'LED2State': ['1'],
                             'LED3State': ['0']
                             }
  OUTPUT_LOAD_ONE_NOSEPOKE = {'Start': [datetime(1970, 1, 1, 0, 0, 0, tzinfo=utc)],
                              'End': [datetime(1970, 1, 1, 0, 0, 12, tzinfo=utc)],
                              'Side': [4],
                              'SideCondition': [1],
                              'SideError': [0],
                              'TimeError': [1],
                              'ConditionError': [1],
                              'LickNumber': [0],
                              'LickContactTime': [None],
                              'LickDuration': [timedelta(seconds=1.5)],
                              'AirState': [0],
                              'DoorState': [1],
                              'LED1State': [0],
                              'LED2State': [1],
                              'LED3State': [0],
                              '_line': [1],
                              }

  INPUT_LOAD_MANY_VISITS_MANY_NOSEPOKES = {
    'Visits': {'ID': ['1', '2', '3', '4'],
               'Animal': ['1', '2', '3', '4'],
               'Start': [datetime(1970, 1, 1, 0, 0, 0, tzinfo=utc),
                         datetime(1970, 1, 1, 0, 0, 0, tzinfo=utc),
                         datetime(1970, 1, 1, 0, 0, 0, tzinfo=utc),
                         datetime(1970, 1, 1, 0, 0, 0, tzinfo=utc),
                         ],
               'End': [datetime(1970, 1, 1, 0, 0, 12, tzinfo=utc),
                       datetime(1970, 1, 1, 0, 0, 12, tzinfo=utc),
                       datetime(1970, 1, 1, 0, 0, 12, tzinfo=utc),
                       datetime(1970, 1, 1, 0, 0, 12, tzinfo=utc),
                       ],
               'Cage': ['1', '1', '4', '4'],
               'Corner': ['1', '2', '1', '2']},
    'Nosepokes': {'VisitID': ['2', '3', '3', '4', '4', '4'],
                  'Start': [datetime(1970, 1, 1, 0, 33, 12, tzinfo=utc),
                            datetime(1970, 1, 1, 0, 33, 2, tzinfo=utc),
                            datetime(1970, 1, 1, 0, 32, 52, tzinfo=utc),
                            datetime(1970, 1, 1, 0, 32, 42, tzinfo=utc),
                            datetime(1970, 1, 1, 0, 32, 32, tzinfo=utc),
                            datetime(1970, 1, 1, 0, 32, 22, tzinfo=utc)],
                     'End': [datetime(1970, 1, 1, 0, 33, 17, tzinfo=utc),
                            datetime(1970, 1, 1, 0, 33, 7, tzinfo=utc),
                            datetime(1970, 1, 1, 0, 32, 57, tzinfo=utc),
                            datetime(1970, 1, 1, 0, 32, 47, tzinfo=utc),
                            datetime(1970, 1, 1, 0, 32, 37, tzinfo=utc),
                            datetime(1970, 1, 1, 0, 32, 27, tzinfo=utc)],
                     'Side': ['3', '6', '5', '8', '7', '8'],
                     'SideCondition': ['0', '1', '-1', '0', '1', '-1'],
                     'SideError': ['0', '0', '1', '0', '0', '1'],
                     'TimeError': ['1', '-1', '0', '1', '-1', '0'],
                     'ConditionError': ['-1', '0', '1', '-1', '0', '1'],
                     'LicksNumber': ['2', '6', '9', '16', '20', '24'],
                     'LicksDuration': ['0.75', '2.25', '3.375', '6.0', '7.5', '9.0'],
                     'AirState': ['1', '0', '1', '0', '1', '0'],
                     'DoorState': ['0', '1', '0', '1', '0', '1'],
                     'LED1State': ['0', '1', '1', '0', '0', '1'],
                     'LED2State': ['1', '0', '0', '1', '1', '0'],
                     'LED3State': ['0', '0', '1', '1', '1', '0'],
                     }
  }
  OUTPUT_LOAD_MANY_VISITS_MANY_NOSEPOKES = {
    'Nosepokes':
        {
          'Start': [datetime(1970, 1, 1, 0, 33, 12, tzinfo=utc),
                    datetime(1970, 1, 1, 0, 32, 52, tzinfo=utc),
                    datetime(1970, 1, 1, 0, 33, 2, tzinfo=utc),
                    datetime(1970, 1, 1, 0, 32, 22, tzinfo=utc),
                    datetime(1970, 1, 1, 0, 32, 32, tzinfo=utc),
                    datetime(1970, 1, 1, 0, 32, 42, tzinfo=utc)],
          'End': [datetime(1970, 1, 1, 0, 33, 17, tzinfo=utc),
                  datetime(1970, 1, 1, 0, 32, 57, tzinfo=utc),
                  datetime(1970, 1, 1, 0, 33, 7, tzinfo=utc),
                  datetime(1970, 1, 1, 0, 32, 27, tzinfo=utc),
                  datetime(1970, 1, 1, 0, 32, 37, tzinfo=utc),
                  datetime(1970, 1, 1, 0, 32, 47, tzinfo=utc)],
          'Side': [3, 5, 6, 8, 7, 8],
          'SideCondition': [0, -1, 1, -1, 1, 0],
          'SideError': [0, 1, 0, 1, 0, 0],
          'TimeError': [1, 0, -1, 0, -1, 1],
          'ConditionError': [-1, 1, 0, 1, 0, -1],
          'LickNumber': [2, 9, 6, 24, 20, 16],
          'LickContactTime': [None, None, None, None, None, None],
          'LickDuration': floatToTimedelta([0.75, 3.375, 2.25, 9.0, 7.5, 6.0]),
          'AirState': [1, 1, 0, 0, 1, 0],
          'DoorState': [0, 0, 1, 1, 0, 1],
          'LED1State': [0, 1, 1, 1, 0, 0],
          'LED2State': [1, 0, 0, 0, 1, 1],
          'LED3State': [0, 1, 0, 0, 1, 1],
          '_line': [1, 3, 2, 6, 5, 4]
        },
    'NosepokeLen': [0, 1, 2, 3],
  }
  MISSING_FIELDS_LOAD_MANY_VISITS_MANY_NOSEPOKES = [None,
                                                    'End',
                                                    'Side',
                                                    'SideCondition',
                                                    'SideError',
                                                    'TimeError',
                                                    'ConditionError',
                                                    ('LicksNumber', 'LickNumber'),
                                                    ('LicksDuration', 'LickDuration'),
                                                    'AirState',
                                                    'DoorState',
                                                    'LED1State',
                                                    'LED2State',
                                                    'LED3State',]


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
                           returns=cage,
                           tracker=None)
    pm._ICData.ICCage = minimock.Mock('Data.ICCage',
                                      returns_func=newCage,
                                      tracker=None)

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
        item = minimock.Mock('ICCage(%s)' % cage, tracker=None)
        item._del_.mock_returns_func = lambda: delCalled.add(cage)
        cages[cage] = item
        return item

    pm._ICData.ICCage = minimock.Mock('Data.ICCage', tracker=None)
    pm._ICData.ICCage.mock_returns_func = newCage

    for i in range(1, 10):
      for j in range(1, i + 1):
        self.cageManager[j] # FIXME: what it is doing?

    self.cageManager._del_()
    for cage in cages:
      self.assertTrue(cage in delCalled)

  def testReadOnly(self):
    self.assertRaises(AttributeError, lambda: setattr(self.cageManager, 'Nonexistingattr', None))


class DataTest(unittest.TestCase):
  def testDel(self):
    ICCage = pm._ICData.ICCage

    def getMockCage(n):
      cage = minimock.Mock('ICCage', tracker=None)
      cage._del_ = lambda: cagesDeleted.add(n)
      return cage

    pm._ICData.ICCage = minimock.Mock('ICCage',
                                      returns_func=getMockCage,
                                      tracker=None)

    deleted = set()
    cagesDeleted = set()
    toDelete = []
    cagesToDelete = []
    data = pm.Data.Data() # XXX: ugly test -> split testing of ICCageManager and Data.__del__
    data._setCageManager(pm._ICData.ICCageManager())

    def makeCloneInjector(cage, label):
      toDelete.append(label)
      cagesToDelete.append(cage)
      cloneInjector = minimock.Mock('CloneInjector', tracker=None)
      def cloneReporter(sourceManager, cageManager, *args):
        cageManager[cage] # FIXME: what is it doing?
        clone = minimock.Mock(label, tracker=None)
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


class MockNodesProvider:
  def getMockNode(self, name):
    mock = minimock.Mock(name, tracker=None)
    mock.clone.returns = mock
    return mock

  def getMockNodeList(self, name, n):
    return [self.getMockNode(name) for _ in range(n)]


class MergerTest(BaseTest, MockNodesProvider):
  def setUp(self):
    self.d1 = pm.Data.Data()
    self.d1._setCageManager(IntIdentityManager())
    self.d2 = pm.Data.Data()
    self.d2._setCageManager(IntIdentityManager())
    self.time1 = datetime(1970, 1, 1, 0, tzinfo=utc)
    self.time2 = datetime(1970, 1, 1, 1, tzinfo=utc)
    self.runSetUpChain()


class MergerOnLoadedLog(MergerTest):
  def _setUp(self):
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

  def testLogMerge(self):
    mm = Merger(self.d1, self.d2, getLog=True)
    self.assertEqual([u'D1', u'D2'],
                     [l.Type for l in mm.getLog(order='DateTime')])

  def testLogFrozen(self):
    mm = Merger(self.d1, self.d2, getLog=True)
    with self.assertRaises(mm.UnableToInsertIntoFrozen):
      mm.insertLog(self.getMockNodeList('LogEntry', 3))


class MergerOnLoadedEnv(MergerTest):
  def _setUp(self):
    self.d1.insertEnv([EnvironmentalConditions(self.time1,
                                               12.5, 255, 1, u'D1', 1)])
    self.d2.insertEnv([EnvironmentalConditions(self.time2,
                                               11.5, 0, 3, u'D2', 1)])

  def testEnvMerge(self):
    mm = Merger(self.d1, self.d2, getEnv=True)
    self.assertEqual([12.5, 11.5],
                     [l.Temperature for l in mm.getEnvironment(order='DateTime')])

  def testEnvFrozen(self):
    mm = Merger(self.d1, self.d2, getEnv=True)
    with self.assertRaises(mm.UnableToInsertIntoFrozen):
      mm.insertLog(self.getMockNodeList('EnvironmentalConditions', 4))


class MergerOnLoadedHw(MergerTest):
  def _setUp(self):
    self.d1.insertHw([UnknownHardwareEvent(self.time2, 42, 1, 2, 3, 44, u'D1', 1)])
    self.d2.insertHw([AirHardwareEvent(self.time1, 1, 2, 3, 1, u'D2', 1)])

  def testHwMerge(self):
    mm = Merger(self.d1, self.d2, getHw=True)
    self.assertEqual([u'D2', u'D1'],
                     [h._source for h in mm.getHardwareEvents(order='DateTime')])

  def testHwFrozen(self):
    mm = Merger(self.d1, self.d2, getHw=True)
    with self.assertRaises(mm.UnableToInsertIntoFrozen):
      mm.insertLog(self.getMockNodeList('HardwareEvent', 7))


class LoaderIntegrationTest(BaseTest, MockNodesProvider):
  LOADER_FLAGS = {}

  def setUp(self):
    try:
      self.data = self.loadData()

    except AttributeError as e:
      #print(e)
      self.skipTest("No data filename")

    except:
      print(self.dataPath())
      raise

    else:
      self.runSetUpChain()

  def loadData(self):
    return pm.Loader(self.dataPath(),
                     **self.LOADER_FLAGS)

  def dataPath(self):
    return os.path.join(self.dataDir(), self.DATA_FILE)

  def dataDir(self):
    return os.path.abspath(os.path.join(os.path.dirname(__file__), 'data'))

  def testDataAreFrozen(self):
    with self.assertRaises(Data.UnableToInsertIntoFrozen):
      self.data.insertVisits(self.getMockNodeList('Visit', 2))

    with self.assertRaises(Data.UnableToInsertIntoFrozen):
      self.data.insertLog(self.getMockNodeList('LogEntry', 2))

    with self.assertRaises(Data.UnableToInsertIntoFrozen):
      self.data.insertEnv(self.getMockNodeList('EnvironmentalConditions', 2))

    with self.assertRaises(Data.UnableToInsertIntoFrozen):
      self.data.insertHw(self.getMockNodeList('HardwareEvent', 2))

  def assertSameDT(self, reference, times):
    self.assertEqual(reference, times)
    self.assertEqual([t.hour for t in reference],
                     [t.hour for t in times])


class LoadLegacyDataTest(LoaderIntegrationTest):
  DATA_FILE = 'legacy_data.zip'

  def testGetStartOrderedVisits_fromDoctests(self):
    self.assertEqual([4, 1, 2],
                     [v.Corner for v in self.data.getVisits(order='Start')])

  def testGetOneMouseVisits_fromDoctests(self):
    self.assertEqual([1],
                     [v.Corner for v in self.data.getVisits(mice='Mickey')])

  def testGetManyMiceOrderedVisits_fromDoctests(self):
    self.assertEqual([4, 1],
                     [v.Corner for v in self.data.getVisits(mice=['Mickey',
                                                                  'Minnie'],
                                                            order='Start')])

  def testGetManyMiceOrderedVisitsGivenAnimalsObject_fromDoctests(self):
    mice = [self.data.getAnimal(m) for m in ['Mickey', 'Minnie']]
    self.assertEqual([4, 1],
                     [v.Corner for v in self.data.getVisits(mice=mice,
                                                            order='Start')])

  def testGetOneMouseVisitsStartTimezones_fromDoctests(self):
    starts = [datetime(2012, 12, 18, 12, 30, 2, 360000, timezone('Etc/GMT-1')),]
    self.assertSameDT(starts,
                      [v.Start for v in self.data.getVisits(mice='Minnie')])

  def testLickNumberNosepokeAttribute(self):
    self.checkAttrOfNosepokes('LickNumber',
                              [0, 1, 2, 3])

  def testLickDurationNosepokeAttribute(self):
    self.checkAttrOfNosepokes('LickDuration',
                              floatToTimedelta([0, 0.075, 0.15, 0.225]))

  def testLickContactTimeNosepokeAttribute(self):
    self.checkAttrOfNosepokes('LickContactTime',
                              [None, None, None, None])


  def checkAttrOfNosepokes(self, attr, expected):
    self.assertEqual(expected,
                     [getattr(n, attr) for v in self.data.getVisits(order='Start') for n in v.Nosepokes])


class GivenLegacyDataLoadedWithEnvData(LoadLegacyDataTest):
  LOADER_FLAGS = {'getEnv': True}

  def testCanBeMerged(self):
    pm.Merger(self.data,
              **self.LOADER_FLAGS)

  def testTemperature(self):
    self.assertEqual([22] * 13,
                     [e.Temperature for e in self.data.getEnvironment()])


  def testIllumination(self):
    self.assertEqual(list(range(100, 113)),
                     [e.Illumination for e in self.data.getEnvironment(order='DateTime')])


class GivenLegacyDataLoadedWithHwData(LoadLegacyDataTest):
  LOADER_FLAGS = {'getHw': True}

  def testHwCageCornerSide(self):
    self.assertEqual([(2, 3, 6),
                      (2, 2, 3),
                      (4, 1, 2),
                      (4, 1, 2),
                      (2, 1, 2),
                      (4, 3, 6),
                      (4, 3, 6),
                      (3, 1, 2),
                      (4, 1, 1),
                      (4, 3, 6),
                      (3, 1, 1),
                      (3, 3, 6),
                      (4, 2, 3),
                      (4, 2, 3),
                      ],
                     [(h.Cage, h.Corner, h.Side) for h in self.data.getHardwareEvents(order='DateTime')])


class GivenLegacyDataLoadedWithLogData(LoadLegacyDataTest):
  LOADER_FLAGS = {'getLog': True}


class LoadLegacyDataWithoutIntelliCageSubdirTest(LoadLegacyDataTest):
  DATA_FILE = 'legacy_data_nosubdir.zip'


class LoadIntelliCagePlus3DataTest(LoaderIntegrationTest):
  DATA_FILE = 'icp3_data.zip'
  LOADER_FLAGS = {'getLog': True,
                  'getEnv': True,
                  'getHw': True}

  def testGetStartOrderedVisits_fromDoctests(self):
    self.assertEqual([1, 2, 3],
                     [v.Corner for v in self.data.getVisits(order='Start')])

  def testGetOneMouseOrderedVisits_fromDoctests(self):
    self.assertEqual([3],
                     [v.Corner for v in self.data.getVisits(mice='Jerry',
                                                            order='Start')])

  def testGetManyMiceOrderedVisits_fromDoctests(self):
    self.assertEqual([1, 3],
                     [v.Corner for v in self.data.getVisits(mice=['Jerry',
                                                                  'Minnie'],
                                                            order='Start')])

  def testOrderedVisitsStartTimezones_fromDoctests(self):
    CET = timezone('Etc/GMT-1')
    starts = [datetime(2012, 12, 18, 12, 13, 14, 139000, CET),
              datetime(2012, 12, 18, 12, 18, 55, 421000, CET),
              datetime(2012, 12, 18, 12, 19, 55, 421000, CET),]
    self.assertSameDT(starts,
                      [v.Start for v in self.data.getVisits(order='Start')])

  def testGetOrderedLog(self):
    self.assertEqual(['Session is started', 'Session is stopped'],
                     [l.Notes for l in self.data.getLog(order='DateTime')])

  def testDoubleOrderedEnv(self):
    self.assertEqual([22.0, 23.6, 22.0, 23.6, 22.0, 23.6, 22.0, 23.6,
                      22.0, 23.6, 22.0, 23.6, 22.0, 23.6, 22.0, 23.6,],
                     [e.Temperature for e in self.data.getEnvironment(order=('DateTime', 'Cage'))])

  def testGetCageByAnimalName(self):
    self.assertEqual(1, self.data.getCage('Minnie'))

  def testGetCageByAnimal(self):
    minnie = self.data.getAnimal('Minnie')
    self.assertEqual(1, self.data.getCage(minnie))

  def testGetOrderedHwTypes(self):
    self.assertEqual(['Air', 'Air', 'LED', 'Door', 'Door', 'LED'],
                     [h.Type for h in self.data.getHardwareEvents(order='DateTime')])

class LoadEmptyDataTest(LoaderIntegrationTest):
  DATA_FILE = 'empty_data.zip'


class GivenArchiveMissingEnvAndHwDataLoadedRequestingThoseData(LoaderIntegrationTest):
  DATA_FILE = 'more_empty_data.zip'
  LOADER_FLAGS = {'getEnv': True,
                  'getHw': True}

  def testGetEnvironmentReturnsEmptyList(self):
    self.assertEqual([],
                     self.data.getEnvironment())

  def testGetHardwareEventsReturnsEmptyList(self):
    self.assertEqual([],
                     self.data.getHardwareEvents())


class LoadRetaggedDataTest(LoaderIntegrationTest):
  DATA_FILE = 'retagged_data.zip'


@unittest.skip('Not implemented yet')
class LoadAnalyserDataTest(LoaderIntegrationTest):
  DATA_FILE = 'analyzer_data.txt'
  LOADER_FLAGS = {'getNpokes': True}


class DataTest(BaseTest, MockNodesProvider):
  def setUp(self):
    self.data = Data()
    self.data._setCageManager(IntIdentityManager())
    self.runSetUpChain()


class OnVisitsLoaded(DataTest):
  def _setUp(self):
    self.visits = self.getMockNodeList('Visit', 2)
    self.data.insertVisits(self.visits)

class OnLogLoaded(DataTest):
  def _setUp(self):
    self.log = self.getMockNodeList('LogEntry', 3)
    self.data.insertLog(self.log)

class OnEnvLoaded(DataTest):
  def _setUp(self):
    self.env = self.getMockNodeList('EnvironmentalConditions', 4)
    self.data.insertEnv(self.env)

class OnHwLoaded(DataTest):
  def _setUp(self):
    self.hw = self.getMockNodeList('HardwareEvent', 5)
    self.data.insertHw(self.hw)

class OnFrozen(OnVisitsLoaded, OnLogLoaded, OnEnvLoaded, OnHwLoaded):
  def _setUp(self):
    self.data.freeze()

  def testInsertVisitRaisesUnableToInsertIntoFrozen(self):
    with self.assertRaises(Data.UnableToInsertIntoFrozen):
      self.data.insertVisits(self.getMockNodeList('Visit', 2))

  def testInsertLogRaisesUnableToInsertIntoFrozen(self):
    with self.assertRaises(Data.UnableToInsertIntoFrozen):
      self.data.insertLog(self.getMockNodeList('LogEntry', 2))

  def testInsertEnvRaisesUnableToInsertIntoFrozen(self):
    with self.assertRaises(Data.UnableToInsertIntoFrozen):
      self.data.insertEnv(self.getMockNodeList('EnvironmentalConditions', 2))

  def testInsertHwRaisesUnableToInsertIntoFrozen(self):
    with self.assertRaises(Data.UnableToInsertIntoFrozen):
      self.data.insertHw(self.getMockNodeList('HardwareEvent', 2))


def getGlobals():
  dataDir = os.path.abspath(os.path.join(os.path.dirname(__file__), 'data'))
  return {
    #XXX: ml_l1 - not sure if data format is valid
    'ml_l1': pm.Loader(os.path.join(dataDir, 'legacy_data.zip')),
    #'ml_a1': pm.Loader(os.path.join(dataDir, 'analyzer_data.txt'), getNpokes=True),
    'ml_icp3': pm.Loader(os.path.join(dataDir, 'icp3_data.zip'),
                      getLog=True, getEnv=True),
    'ml_empty': pm.Loader(os.path.join(dataDir, 'empty_data.zip')),
    'ml_retagged': pm.Loader(os.path.join(dataDir, 'retagged_data.zip')),
  }

if __name__ == '__main__':
  unittest.main()
