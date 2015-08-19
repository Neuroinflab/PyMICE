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
                       MockStrDictManager, MockAnimalManager, BaseTest


class TestZipLoader(BaseTest):
  def setUp(self):
    self.sideManager = MockIntDictManager()
    self.cageManager = MockCageManager({'getSideManager': {(4, 2): self.sideManager}})
    self.animalManager = MockAnimalManager()
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
                        ('Corner', [(2, self.cageManager.Cls),
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

    self.assertEqual(self.animalManager.sequence, [('getByTag', '10')])
    self.assertEqual(self.cageManager.sequence[0], ('getCageCorner', 1, 2))

  #@unittest.skip('botak')
  def testLoadManyVisitsWithMissingValues(self):
    def toStrings(seq):
      return [str(x) if x is not None else None for x in seq]

    def floatToStrings(seq):
      return ['%.3f' % x if x is not None else None for x in seq]

    def floatToTimedelta(seq):
      return [timedelta(seconds=x) if x is not None else None for x in seq]

    nVisits = 10
    vNumbers = range(1, nVisits + 1)
    animals = [str(1 + i % 2) for i in vNumbers]
    start = datetime(1970, 1, 1, tzinfo=utc)
    starts = [start + timedelta(seconds=10 * i) for i in vNumbers]
    ends = [start + timedelta(seconds=15 + 10 * i) for i in vNumbers]
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

    visits = self.loader.loadVisits({'VisitID': toStrings(vNumbers),
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
                                     })
    for name, tests in [('Animal', toStrings(animals)),
                        ('Start', starts),
                        ('End', ends),
                        ('Module', modules),
                        ('Cage', cages),
                        ('Corner', corners),
                        ('CornerCondition', conditions),
                        ('PlaceError', errors),
                        ('AntennaNumber', aNumbers),
                        ('AntennaDuration', floatToTimedelta(aDurations)),
                        ('PresenceNumber', pNumbers),
                        ('PresenceDuration', floatToTimedelta(pDurations)),
                        ('VisitSolution', solutions),
                        ('_source', [self.source] * nVisits),
                        ('_line', vNumbers),
                        ('Nosepokes', [None] * nVisits),
                        ]:
      self.checkAttributeSeq(visits, name, tests)

    #self.assertEqual(self.animalManager.sequence, [('getByTag', '10')])
    #self.assertEqual(self.cageManager.sequence[0], ('getCageCorner', 1, 2))

if __name__ == '__main__':
  unittest.main()