#!/usr/bin/env python
# encoding: utf-8
###############################################################################
#                                                                             #
#    PyMICE library                                                           #
#                                                                             #
#    Copyright (C) 2012-2015 Jakub M. Kowalski, S. Łęski (Laboratory of       #
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

from ._ICNodesBase import (BaseNodeMetaclass, BaseNode_del_, \
                           VisitMetaclass, DurationAware, getTimeString)

class BaseNode(object, metaclass=BaseNodeMetaclass):
  __slots__ = ()
  _del_ = BaseNode_del_

class Visit(BaseNode, DurationAware, metaclass=VisitMetaclass):
  __slots__ = ('Start', 'Corner', 'Animal', 'End', 'Module', 'Cage',
               'CornerCondition', 'PlaceError',
               'AntennaNumber', 'AntennaDuration',
               'PresenceNumber', 'PresenceDuration',
               'VisitSolution',
               '_source', '_line',
               'Nosepokes')


  def __init__(self, Start, Corner, Animal, End, Module, Cage,
               CornerCondition, PlaceError,
               AntennaNumber, AntennaDuration, PresenceNumber, PresenceDuration,
               VisitSolution,
               _source, _line,
               Nosepokes):
    self.__Start = Start
    self.__Corner = Corner
    self.__Animal = Animal
    self.__End = End
    self.__Module = Module
    self.__Cage = Cage
    self.__CornerCondition = CornerCondition
    self.__PlaceError = PlaceError
    self.__AntennaNumber = AntennaNumber
    self.__AntennaDuration = AntennaDuration
    self.__PresenceNumber = PresenceNumber
    self.__PresenceDuration = PresenceDuration
    self.__VisitSolution = VisitSolution
    self.___source = _source
    self.___line = _line
    self.__Nosepokes = Nosepokes
    if Nosepokes is not None:
      for nosepoke in Nosepokes:
        nosepoke._bindToVisit(self)

  def clone(self, sourceManager, cageManager, animalManager):
    source = sourceManager[self.___source]
    animal = animalManager[self.__Animal]
    cage = cageManager[self.__Cage]
    corner = cage[self.__Corner]
    nosepokes = tuple(n.clone(sourceManager, corner) for n in self.__Nosepokes) if self.__Nosepokes is not None else None
    return self.__class__(self.__Start, corner, animal,
                          self.__End, self.__Module, cage,
                          self.__CornerCondition, self.__PlaceError,
                          self.__AntennaNumber, self.__AntennaDuration,
                          self.__PresenceNumber, self.__PresenceDuration,
                          self.__VisitSolution, source,
                          self.___line, nosepokes)

  def _del_(self):
    if self.__Nosepokes:
      for nosepoke in self.__Nosepokes:
        nosepoke._del_()

    super(Visit, self)._del_()

  # derivatives
  @property
  def NosepokeNumber(self):
    if self.__Nosepokes is not None:
      return len(self.__Nosepokes)

  def __repr__(self):
    return '< Visit of "%s" to corner #%d of cage #%d (at %s) >' % \
           (self.__Animal, self.__Corner, self.__Cage,
            getTimeString(self.__Start))