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
import unittest

from datetime import datetime, timedelta
from pytz import utc

from pymice.ICNodes import (Animal, Visit, Nosepoke,
                            LogEntry, EnvironmentalConditions,
                            AirHardwareEvent, DoorHardwareEvent,
                            LedHardwareEvent, UnknownHardwareEvent,
                            NamedInt)
from TestTools import (allInstances, Mock, MockIntDictManager,
                       MockStrDictManager, MockCloneable,
                       BaseTest)


if sys.version_info >= (3, 0):
  unicode = str


class ICNodeTest(BaseTest):
  def checkReadOnly(self, obj):
    for attr in self.attributes:
      try:
        self.assertRaises(AttributeError, lambda: setattr(obj, attr, attr))

      except AssertionError:
        print(attr)
        raise

  def checkDel(self, obj, skip=()):
    slots = set('_' + cls.__name__ + s if s.startswith('__') else s \
                for cls in obj.__class__.__mro__ if hasattr(cls, '__slots__')\
                for s in cls.__slots__)
    for attr in slots:
      if attr in skip:
        continue

      try:
        getattr(obj, attr)

      except AttributeError:
        print(attr)
        raise

    obj._del_()

    for attr in slots:
      try:
        self.assertRaises(AttributeError,
                          lambda: getattr(obj, attr))
      except AssertionError:
        print(attr)
        raise

  def checkSlots(self, obj):
    self.assertRaises(AttributeError,
                      lambda: setattr(obj, 'nonexistentAttribute', None))
    self.assertFalse('__dict__' in dir(obj))


class TestAnimal(ICNodeTest):
  attributes = ['Name', 'Tag', 'Sex', 'Notes']

  def setUp(self):
    self.mickey = Animal(u'Mickey', frozenset({'2'}), u'male', frozenset({u'bla'}))

  def testCreate(self):
    self.assertEqual(self.mickey.Name, 'Mickey')
    self.assertEqual(self.mickey.Tag, {'2'})
    self.assertEqual(self.mickey.Sex, 'male')
    self.assertEqual(self.mickey.Notes, {'bla'})


  def testFromRow(self):
    jerry = Animal.fromRow('Jerry', '1', None, None)
    self.checkAttributes(jerry,
                         [('Name', 'Jerry', unicode),
                          ('Tag', {'1'}, frozenset),
                          'Sex',
                          ('Notes', frozenset(), frozenset)
                         ])
    self.assertTrue(allInstances(jerry.Tag, unicode))

    mickey = Animal.fromRow('Mickey', '2', 'male', 'note')
    self.checkAttributes(mickey,
                         [('Name', 'Mickey', unicode),
                          ('Tag', {'2'}, frozenset),
                          ('Sex', 'male', unicode),
                          ('Notes', {'note'}, frozenset)
                         ])
    self.assertTrue(allInstances(mickey.Tag, unicode))
    self.assertTrue(allInstances(mickey.Notes, unicode))

  def testClone(self):
    animal = self.mickey.clone()
    for attr in self.attributes:
      if attr != 'Nosepokes':
        self.assertEqual(getattr(animal, attr),
                         getattr(self.mickey, attr))

  def testEq(self):
    self.assertTrue(self.mickey == Animal.fromRow('Mickey', '2'))
    self.assertTrue(Animal.fromRow('Mickey', '2') == self.mickey)
    self.assertFalse(self.mickey == Animal.fromRow('Jerry', '2'))
    self.assertFalse(self.mickey == Animal.fromRow('Mickey', '2', Sex='female'))

    animal = Animal.fromRow(u'b\xf3br', '1')
    if sys.version_info < (3, 0):
      self.assertTrue(animal == 'b\xc3\xb3br')

    self.assertFalse(animal == 'bobr')

    self.assertTrue(animal == u'b\xf3br')
    self.assertFalse(animal == u'b\xc3\xb3br')

  def testNeq(self):
    self.assertTrue(self.mickey != Animal.fromRow('Jerry', '2'))
    self.assertTrue(self.mickey != Animal.fromRow('Mickey', '2', Sex='female'))
    self.assertFalse(self.mickey != Animal.fromRow('Mickey', '2'))

    animal = Animal(u'b\xf3br', '1')
    if sys.version_info < (3, 0):
      self.assertFalse(animal != 'b\xc3\xb3br')
    self.assertTrue(animal != 'bobr')
    self.assertFalse(animal != u'b\xf3br')
    self.assertTrue(animal != u'b\xc3\xb3br')

  def testHash(self):
    self.assertEqual(hash(self.mickey), hash('Mickey'))

  @unittest.skipIf(sys.version_info >= (3, 0),
                   'Python3: tested by .testUnicode()')
  def testStr(self):
    animal = Animal.fromRow(u'b\xf3br', '1')
    self.assertEqual(str(animal), 'b\xc3\xb3br')
    self.assertIsInstance(str(animal), str)

  def testUnicode(self):
    animal = Animal.fromRow(u'b\xf3br', '1')
    self.assertEqual(unicode(animal), u'b\xf3br')
    self.assertIsInstance(unicode(animal), unicode)


  def testMerge(self):
    mouse = Animal.fromRow('Mickey', '1')
    mouse.merge(self.mickey)
    self.assertEqual(mouse.Sex, 'male')
    self.assertEqual(mouse.Notes, {'bla'})
    self.assertEqual(mouse.Tag, {'1', '2'})
    self.assertIsInstance(mouse.Tag, frozenset)

    mouse.merge(Animal.fromRow('Mickey', '1'))
    self.assertEqual(mouse.Sex, 'male')


    self.assertRaises(Animal.DifferentMouseError,
                      lambda: Animal.fromRow('Minnie', '1').merge(self.mickey))
    self.assertRaises(Animal.DifferentMouseError,
                      lambda: Animal.fromRow('Mickey', '1', 'female').merge(self.mickey))

    mouse = Animal.fromRow('Mickey', '1', Notes='ble')
    mouse.merge(self.mickey)
    self.assertEqual(mouse.Notes, {'ble', 'bla'})
    mouse.merge(self.mickey)
    self.assertEqual(mouse.Notes, {'ble', 'bla'})

  def testRepr(self):
    self.assertEqual(repr(self.mickey), u'< Animal Mickey (male; Tag: 2) >')
    mouse = Animal.fromRow('Jerry', '1')
    self.assertEqual(repr(mouse), u'< Animal Jerry (Tag: 1) >')
    mouse.merge(Animal.fromRow('Jerry', ' 2'))
    self.assertEqual(repr(mouse), u'< Animal Jerry (Tags: 1, 2) >')

  def testReadOnly(self):
    self.checkReadOnly(self.mickey)

  def testSlots(self):
    self.checkSlots(self.mickey)

  def testDel(self):
    self.checkDel(self.mickey)


class TestVisit(ICNodeTest):
  attributes = ('Start', 'Corner', 'End', 'Module', 'Cage',
                'CornerCondition', 'PlaceError',
                'AntennaNumber', 'AntennaDuration',
                'PresenceNumber', 'PresenceDuration',
                'VisitSolution',
                '_source', '_line',
                'Nosepokes')

  def setUp(self):
    self.start = datetime(1970, 1, 1, 0, 0, 0, tzinfo=utc)
    self.end = datetime(1970, 1, 1, 0, 5, 15, tzinfo=utc)
    self.nosepokes = tuple(MockCloneable(Duration = timedelta(seconds=10.25 * i),
                                         LickNumber = i - 1,
                                         LickDuration = timedelta(seconds=0.25 * i),
                                         LickContactTime= timedelta(seconds=0.125 * i))\
                           for i in range(1, 5))
    self.visit = Visit(self.start, 2, 'animal', self.end, 'mod', 4,
                       1, 0,
                       2, timedelta(seconds=12.125), 7, timedelta(seconds=8.5),
                       0,
                       'source', 1,
                       self.nosepokes,
                       )
    self.minimalVisit = Visit(self.start, 2, 'animal', None, None, -1,
                              None, None,
                              None, None, None, None,
                              None,
                              None, None,
                              None)

  def testCreate(self):
    self.checkAttributes(self.minimalVisit, [('Start', self.start),
                                             ('Corner', 2),
                                             ('Animal', 'animal'),
                                             ('Cage', -1),
                                             'End', 'Module',
                                             'CornerCondition', 'PlaceError',
                                             'AntennaNumber', 'AntennaDuration',
                                             'PresenceNumber', 'PresenceDuration',
                                             'VisitSolution',
                                             '_source', '_line',
                                             'Nosepokes',
                                             ])

    self.checkAttributes(self.visit, [('Start', self.start),
                                      ('Corner', 2),
                                      ('Animal', 'animal'),
                                      ('End', self.end),
                                      ('Module', 'mod'),
                                      ('Cage', 4),
                                      ('CornerCondition', 1),
                                      ('PlaceError', 0),
                                      ('AntennaNumber', 2),
                                      ('AntennaDuration', timedelta(seconds=12.125)),
                                      ('PresenceNumber', 7),
                                      ('PresenceDuration', timedelta(seconds=8.5)),
                                      ('VisitSolution', 0),
                                      ('_source', 'source'),
                                      ('_line', 1),
                                      ('Nosepokes', self.nosepokes),
                                      ])

  def testClone(self):
    cageManager = MockIntDictManager()
    sourceManager = MockStrDictManager()
    animalManager = MockStrDictManager()
    visit = self.visit.clone(sourceManager, cageManager, animalManager)
    self.checkObjectsEquals(visit, self.visit,
                            skip=['Nosepokes'])

    for nosepoke, clonedNosepoke in zip(self.visit.Nosepokes,
                                        visit.Nosepokes):
      self.assertEqual(nosepoke.sequence[-1], ('clone', sourceManager, cageManager.items[4].items[2]))
      self.assertIs(clonedNosepoke._cloneOf, nosepoke)

    self.assertTrue(('__getitem__', 4) in cageManager.sequence)
    self.assertTrue(('__getitem__', 2) in cageManager.items[4].sequence)
    self.assertIs(visit.Cage, cageManager.items[4])
    self.assertIs(visit.Corner, cageManager.items[4].items[2])

    self.assertEqual(animalManager.sequence, [('__getitem__', 'animal')])
    self.assertIsInstance(visit.Animal, animalManager.Cls)

    self.assertEqual(sourceManager.sequence, [('__getitem__', 'source')])
    self.assertIsInstance(visit._source, sourceManager.Cls)

  def testCloneNoNosepokes(self):
    cageManager = MockIntDictManager()
    sourceManager = MockStrDictManager()
    animalManager = MockStrDictManager()

    clone = self.minimalVisit.clone(sourceManager, cageManager, animalManager)
    self.checkObjectsEquals(self.minimalVisit, clone)

  def testReadOnly(self):
    self.checkReadOnly(self.visit)

  def testSlots(self):
    self.checkSlots(self.visit)

  def testNosepokes(self):
    for nosepoke in self.nosepokes:
      self.assertEqual(nosepoke.sequence, [('_bindToVisit', self.visit)])
      self.assertIs(nosepoke.sequence[0][1], self.visit)

  def testDel(self):
    self.checkDel(self.visit)
    for nosepoke in self.nosepokes:
      self.assertEqual(nosepoke.sequence[-1], '_del_')

  def testDuration(self):
    self.assertEqual(self.visit.Duration, timedelta(seconds=315))
    self.assertRaises(Visit.DurationCannotBeCalculatedError, lambda: self.minimalVisit.Duration)

  def testNosepokeNumber(self):
    self.assertEqual(self.visit.NosepokeNumber, 4)
    self.assertIs(self.minimalVisit.NosepokeNumber, None)

  def testNosepokeDuration(self):
    self.assertEqual(self.visit.NosepokeDuration, timedelta(seconds=102.5))
    self.assertIs(self.minimalVisit.NosepokeDuration, None)

  def testLickNumber(self):
    self.assertEqual(self.visit.LickNumber, 6)
    self.assertIs(self.minimalVisit.LickNumber, None)

  def testLickDuration(self):
    self.assertEqual(self.visit.LickDuration, timedelta(seconds=2.5))
    self.assertIs(self.minimalVisit.LickDuration, None)

  def testLickContactTime(self):
    self.assertEqual(self.visit.LickContactTime, timedelta(seconds=1.25))
    self.assertIs(self.minimalVisit.LickContactTime, None)

  def testRepr(self):
    self.assertEqual(repr(self.visit),
                     u'< Visit of "animal" to corner #2 of cage #4 (at 1970-01-01 00:00:00.000) >')


class TestNosepoke(ICNodeTest):
  attributes = ('Start', 'End', 'Side',
                'LickNumber', 'LickContactTime', 'LickDuration',
                'SideCondition', 'SideError', 'TimeError', 'ConditionError',
                'AirState', 'DoorState', 'LED1State', 'LED2State', 'LED3State',
                '_source', '_line',
                'Visit',
                )

  def setUp(self):
    self.start = datetime(1970, 1, 1, 0, 0, 0, tzinfo=utc)
    self.end = datetime(1970, 1, 1, 0, 5, 15, tzinfo=utc)
    self.nosepoke = Nosepoke(self.start, self.end, 2,
                             2, timedelta(seconds=0.125), timedelta(seconds=0.5),
                             -1, 1, 0, 1,
                             0, 1, 0, 1, 0,
                             'src', 11)

  def testCreate(self):
    self.checkAttributes(self.nosepoke,
                         [('Start', self.start, datetime),
                          ('End', self.end, datetime),
                          ('Side', 2),
                          ('LickNumber', 2),
                          ('LickContactTime', timedelta(seconds=0.125)),
                          ('LickDuration', timedelta(seconds=0.5)),
                          ('SideCondition', -1),
                          ('SideError', 1),
                          ('TimeError', 0),
                          ('ConditionError', 1),
                          ('AirState', 0),
                          ('DoorState', 1),
                          ('LED1State', 0),
                          ('LED2State', 1),
                          ('LED3State', 0),
                          ('_source', 'src'),
                          ('_line', 11),
                         ])

  def testClone(self):
    sideManager = MockIntDictManager()
    sourceManager = MockStrDictManager()
    visit = Mock(Cage=7, Corner=1)
    self.nosepoke._bindToVisit(visit)
    nosepoke = self.nosepoke.clone(sourceManager, sideManager)

    self.checkObjectsEquals(nosepoke, self.nosepoke,
                            skip=['Visit'])

    self.assertEqual(sideManager.sequence, [('__getitem__', 2)])
    self.assertIsInstance(nosepoke.Side, sideManager.Cls)

    self.assertEqual(sourceManager.sequence, [('__getitem__', 'src')])
    self.assertIsInstance(nosepoke._source, sourceManager.Cls)

    sideManager = MockIntDictManager()
    sourceManager = MockStrDictManager()
    noSideNosepoke = Nosepoke(self.start, *[None]*14 + ['src', 123])
    nosepoke = noSideNosepoke.clone(sourceManager, sideManager)
    self.checkAttributes(nosepoke, [('Start', self.start),
                                    'End', 'Side',
                                    'LickNumber', 'LickContactTime', 'LickDuration',
                                    'SideCondition', 'SideError', 'TimeError', 'ConditionError',
                                    'AirState', 'DoorState', 'LED1State', 'LED2State', 'LED3State',
                                    ('_source', 'src', sourceManager.Cls),
                                    ('_line', 123),
                                    'Door'
                                    ])
    self.assertEqual(sideManager.sequence, [])
    self.assertEqual(sourceManager.sequence, [('__getitem__', 'src')])

  def testReadOnly(self):
    self.checkReadOnly(self.nosepoke)

  def testSlots(self):
    self.checkSlots(self.nosepoke)

  def testDel(self):
    self.checkDel(self.nosepoke, skip={'_Nosepoke__Visit'})

  def testVisit(self):
    self.assertRaises(AttributeError, lambda: self.nosepoke.Visit)
    visit = object()
    self.nosepoke._bindToVisit(visit)
    self.assertIs(self.nosepoke.Visit, visit)
    self.assertRaises(AttributeError,
                      lambda: setattr(self.nosepoke, 'Visit', 12))

  def testDuration(self):
    self.assertEqual(self.nosepoke.Duration, timedelta(seconds=315))

  def testDoor(self):
    self.assertEqual(self.nosepoke.Door, 'right')

  def testRepr(self):
    self.assertEqual(repr(self.nosepoke),
                     u'< Nosepoke to right door (at 1970-01-01 00:00:00.000) >')


class TestLogEntry(ICNodeTest):
  attributes = ('DateTime', 'Category', 'Type',
                'Cage', 'Corner', 'Side', 'Notes')
  def setUp(self):
    self.time = datetime(1970, 1, 1, 0, 0, 0, tzinfo=utc)
    self.logs = [LogEntry(*row) for row in [
      (self.time, 'cat1', 'tpe1', 3, 2, 3, None, 'src1', 123),
      (self.time, 'cat2', 'tpe2', 3, 1, 2, 'nts2', 'src2', 124),
      (self.time, 'cat3', 'tpe3', 3, 1, None, 'nts3', 'src3', 125),
      (self.time, 'cat4', 'tpe4', 1, None, None, 'nts4', 'src4', 126),
      (self.time, 'cat5', 'tpe5', None, None, None, 'nts5', 'src5', 127),
    ]]

  def testCreate(self):
    n = len(self.logs)
    ns = range(1, n + 1)
    for name, tests in [('DateTime', [self.time] * n),
                        ('Category', ['cat%d' % i for i in ns]),
                        ('Type', ['tpe%d' % i for i in ns]),
                        ('Cage', [3, 3, 3, 1, None]),
                        ('Corner', [2, 1, 1, None, None]),
                        ('Side', [3, 2, None, None, None]),
                        ('Notes', ['nts%d' % i if i != 1 else None for i in ns]),
                        ('_source', ['src%d' %i for i in ns]),
                        ('_line', [122 + i for i in ns])]:
      self.checkAttributeSeq(self.logs, name, tests)

  def testClone(self):
    for log in self.logs:
      cageManager = MockIntDictManager()
      sourceManager = MockStrDictManager()
      clone = log.clone(sourceManager, cageManager)
      self.checkObjectsEquals(log, clone)

      self.assertEqual(sourceManager.sequence, [('__getitem__', log._source)])
      self.assertIsInstance(clone._source, sourceManager.Cls)

      if log.Cage is not None:
        self.assertTrue(('__getitem__', log.Cage) in cageManager.sequence)
        self.assertIs(clone.Cage, cageManager.items[log.Cage])

        if log.Corner is not None:
          self.assertTrue(('__getitem__', log.Corner) in clone.Cage.sequence)
          self.assertIs(clone.Corner, clone.Cage.items[log.Corner])

          if log.Side is not None:
            self.assertTrue(('__getitem__', log.Side) in clone.Corner.sequence)
            self.assertIs(clone.Side, clone.Corner.items[log.Side])

  def testReadOnly(self):
    for log in self.logs:
      self.checkReadOnly(log)

  def testSlots(self):
    for log in self.logs:
      self.checkSlots(log)

  def testDel(self):
    for log in self.logs:
      self.checkDel(log)

  def testDoor(self):
    self.checkAttributeSeq(self.logs, 'Door', ['left', 'right', None, None, None])

  def testRepr(self):
    self.assertEqual(list(map(repr, self.logs)),
                     ['< Log cat%d, tpe%d (at 1970-01-01 00:00:00.000) >' % (i, i)\
                      for i in range(1, len(self.logs) + 1)])


class TestEnvironmentalConditions(ICNodeTest):
  attributes = ('DateTime', 'Temperature', 'Illumination', 'Cage',
                '_source', '_line')
  def setUp(self):
    self.time = datetime(1970, 1, 1, tzinfo=utc)
    self.env = EnvironmentalConditions(self.time, 21.5, 255, 2, 'src', 1)

  def testCreate(self):
    self.checkAttributes(self.env, [('DateTime', self.time),
                                    ('Temperature', 21.5),
                                    ('Illumination', 255),
                                    ('Cage', 2),
                                    ('_source', 'src'),
                                    ('_line', 1),])

  def testClone(self):
    cageManager = MockIntDictManager()
    sourceManager = MockStrDictManager()
    clone = self.env.clone(sourceManager, cageManager)
    self.checkObjectsEquals(self.env, clone)
    self.assertIs(clone.Cage, cageManager.items[2])
    self.assertIsInstance(clone._source, sourceManager.Cls)

  def testReadOnly(self):
    self.checkReadOnly(self.env)

  def testSlots(self):
    self.checkSlots(self.env)

  def testDel(self):
    self.checkDel(self.env)

  def testRepr(self):
    self.assertEqual(repr(self.env),
                     '< Illumination: 255, Temperature: 21.5 (at 1970-01-01 00:00:00.000) >')
    self.assertEqual(repr(EnvironmentalConditions(self.time, 1.0, 0, 1, 'src', 1)),
                     '< Illumination:   0, Temperature:  1.0 (at 1970-01-01 00:00:00.000) >')



class HardwareEventTest(object):
  attributes = ('DateTime', 'Cage', 'Corner', 'Side', 'State',
                '_source', '_line')

  def setUp(self):
    self.time = datetime(1970, 1, 1, tzinfo=utc)
    self.hws = [self.cls(self.time, 2, 1, 1, 0, 'src1', 123),
                self.cls(self.time, 3, 2, 4, 1, 'src2', 124),
                self.cls(self.time, 4, 3, None, 0, 'src3', 125),
                self.cls(self.time, 5, 4, None, 1, 'src4', 126)]

  def testCreate(self):
    n = len(self.hws)
    ns = range(1, n + 1)
    for name, tests in [('DateTime', [self.time] * n),
                        ('Cage', [1 + i for i in ns]),
                        ('Corner', ns),
                        ('Side', [1, 4, None, None]),
                        ('State', [0, 1, 0, 1]),
                        ('_source', ['src%d' %i for i in ns]),
                        ('_line', [122 + i for i in ns])]:
      self.checkAttributeSeq(self.hws, name, tests)

    self._checkTypeAttr()

  def testSlots(self):
    for hw in self.hws:
      self.checkSlots(hw)

  def testReadOnly(self):
    for hw in self.hws:
      self.checkReadOnly(hw)

  def testDel(self):
    for hw in self.hws:
      self.checkDel(hw)

  def testDoor(self):
    self.checkAttributeSeq(self.hws, 'Door', ['left', 'right', None, None])

  def testClone(self):
    for hw in self.hws:
      cageManager = MockIntDictManager()
      sourceManager = MockStrDictManager()
      clone = hw.clone(sourceManager, cageManager)
      self.checkObjectsEquals(hw, clone)
      self.assertIs(hw.__class__, clone.__class__)

      self.assertIsInstance(clone._source, sourceManager.Cls)
      if hw.Cage is not None:
        self.assertIs(clone.Cage, cageManager.items[hw.Cage])

        if hw.Corner is not None:
          self.assertIs(clone.Corner, clone.Cage.items[hw.Corner])

          if hw.Side is not None:
            self.assertIs(clone.Side, clone.Corner.items[hw.Side])

  def testRepr(self):
    for hw, hwRepr in zip(self.hws, self.reprs):
      self.assertEqual(repr(hw), hwRepr)

  def _checkTypeAttr(self):
    Type = self.hws[0].Type
    for hw in self.hws:
      self.assertIs(hw.Type, Type)

    self.assertEqual(self.typeStr, str(Type))


class AirEventTest(HardwareEventTest, ICNodeTest):
  cls = AirHardwareEvent
  typeStr = 'Air'
  reprs = ['< AirEvent: 0 (at 1970-01-01 00:00:00.000) >',
           '< AirEvent: 1 (at 1970-01-01 00:00:00.000) >',
           '< AirEvent: 0 (at 1970-01-01 00:00:00.000) >',
           '< AirEvent: 1 (at 1970-01-01 00:00:00.000) >',]


class DoorEventTest(HardwareEventTest, ICNodeTest):
  cls = DoorHardwareEvent
  typeStr = 'Door'
  reprs = ['< DoorEvent: 0 (at 1970-01-01 00:00:00.000) >',
           '< DoorEvent: 1 (at 1970-01-01 00:00:00.000) >',
           '< DoorEvent: 0 (at 1970-01-01 00:00:00.000) >',
           '< DoorEvent: 1 (at 1970-01-01 00:00:00.000) >',]


class LedEventTest(HardwareEventTest, ICNodeTest):
  cls = LedHardwareEvent
  typeStr = 'LED'
  reprs = ['< LedEvent: 0 (at 1970-01-01 00:00:00.000) >',
           '< LedEvent: 1 (at 1970-01-01 00:00:00.000) >',
           '< LedEvent: 0 (at 1970-01-01 00:00:00.000) >',
           '< LedEvent: 1 (at 1970-01-01 00:00:00.000) >',]


class UnknownEventTest(HardwareEventTest, ICNodeTest):
  attributes = HardwareEventTest.attributes + ('Type',)
  def setUp(self):
    self.time = datetime(1970, 1, 1, tzinfo=utc)
    self.hws = [self.cls(self.time, 0, 2, 1, 1, 0, 'src1', 123),
                self.cls(self.time, 1, 3, 2, 4, 1, 'src2', 124),
                self.cls(self.time, 2, 4, 3, None, 0, 'src3', 125),
                self.cls(self.time, 3, 5, 4, None, 1, 'src4', 126)]

  cls = UnknownHardwareEvent
  reprs = ['< UnknownHardwareEvent(0): 0 (at 1970-01-01 00:00:00.000) >',
           '< UnknownHardwareEvent(1): 1 (at 1970-01-01 00:00:00.000) >',
           '< UnknownHardwareEvent(2): 0 (at 1970-01-01 00:00:00.000) >',
           '< UnknownHardwareEvent(3): 1 (at 1970-01-01 00:00:00.000) >',]

  def _checkTypeAttr(self):
    self.checkAttributeSeq(self.hws, 'Type', range(len(self.hws)))


class NamedIntTest(unittest.TestCase):
  def testNamedInt(self):
    for i, name in enumerate(['', 'a', 'b', 'class']):
      self.checkNamedInt(i, name)

  def checkNamedInt(self, n, name):
    namedInt = NamedInt(n, name)
    self.assertEqual(n, namedInt)
    self.assertEqual(name, str(namedInt))
    self.assertEqual(name, unicode(namedInt))
    namedInt2 = eval(repr(namedInt))
    self.assertEqual(namedInt, namedInt2)
    self.assertEqual(str(namedInt), str(namedInt2))



if __name__ == '__main__':
  unittest.main()
