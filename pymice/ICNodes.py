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

import sys

from ._Tools import toDt
from ._ICNodesBase import DurationAware, getTimeString

if sys.version_info >= (3, 0):
  from ._ICNodes3 import BaseNode, Visit
  unicode = str
  basestring = str

else:
  from ._ICNodes2 import BaseNode, Visit


class SideAware(object):
  __slots__ = ()

  @property
  def Door(self):
    side = self.Side
    if side is not None:
      return 'left' if side % 2 == 1 else 'right'


class Animal(BaseNode):
  class DifferentMouseError(ValueError):
    pass

  __slots__ = ('Name', 'Tag', 'Sex', 'Notes')

  def __init__(self, Name, Tag, Sex=None, Notes=None):
    self.__Name = Name
    self.__Tag = Tag
    self.__Sex = Sex
    self.__Notes = Notes if isinstance(Notes, frozenset) else frozenset() if Notes is None else frozenset({unicode(Notes)})

  @classmethod
  def fromRow(cls, Name, Tag, Sex=None, Notes=None):
    return cls(unicode(Name),
               frozenset({unicode(Tag.strip())}),
               None if Sex is None else unicode(Sex),
               Notes)

  def clone(self):
    return self.__class__(self.__Name,
                          self.__Tag,
                          self.__Sex,
                          self.__Notes)

  def __eq__(self, other):
    if isinstance(other, basestring):
      return other.__class__(self) == other

    if self.__Name != other.__Name:
      return False

    if self.__Sex == other.__Sex or other.__Sex is None or self.__Sex is None:
      return True

    return NotImplemented

  def __ne__(self, other):
    if isinstance(other, basestring):
      return other.__class__(self) != other

    if self.__Name != other.__Name:
      return True

    if self.__Sex == other.__Sex or other.__Sex is None or self.__Sex is None:
      return False

    return NotImplemented

  def __hash__(self):
    return self.__Name.__hash__()


  if sys.version_info >= (3, 0):
    def __str__(self):
      return self.__Name

  else:
    def __str__(self):
      return self.__Name.encode('utf-8')

    def __unicode__(self):
      return self.__Name

  def __repr__(self):
    result = '< Animal %s (' % self.Name
    if self.__Sex is not None:
      result += '%s; ' % self.Sex

    result += 'Tag: ' if len(self.__Tag) == 1 else 'Tags: '
    result += ', '.join(str(t) for t in sorted(self.__Tag))
    return result + ') >'

  def merge(self, other):
    if self != other:
      raise self.DifferentMouseError

    if self.__Sex is None:
      self.__Sex = other.__Sex

    self.__Notes = self.__Notes | other.__Notes
    self.__Tag = self.__Tag | other.__Tag





class Nosepoke(BaseNode, SideAware, DurationAware):
  __slots__ = ('Start', 'End', 'Side',
                'LickNumber', 'LickContactTime', 'LickDuration',
                'SideCondition', 'SideError', 'TimeError', 'ConditionError',
                'AirState', 'DoorState', 'LED1State', 'LED2State', 'LED3State',
                '_source', '_line',
                'Visit',
                )

  def __init__(self, Start, End, Side,
               LickNumber, LickContactTime, LickDuration,
               SideCondition, SideError, TimeError, ConditionError,
               AirState, DoorState, LED1State, LED2State, LED3State,
               _source, _line):
    self.__Start = Start
    self.__End = End
    self.__Side = Side
    self.__LickNumber = LickNumber
    self.__LickContactTime = LickContactTime
    self.__LickDuration = LickDuration
    self.__SideCondition = SideCondition
    self.__SideError = SideError
    self.__TimeError = TimeError
    self.__ConditionError = ConditionError
    self.__AirState = AirState
    self.__DoorState = DoorState
    self.__LED1State = LED1State
    self.__LED2State = LED2State
    self.__LED3State = LED3State
    self.___source = _source
    self.___line = _line

  def clone(self, sourceManager, sideManager):
    side = sideManager[self.__Side] if self.__Side is not None else None
    source = sourceManager[self.___source]
    return self.__class__(self.__Start, self.__End, side,
                          self.__LickNumber, self.__LickContactTime, self.__LickDuration,
                          self.__SideCondition, self.__SideError, self.__TimeError, self.__ConditionError,
                          self.__AirState, self.__DoorState, self.__LED1State, self.__LED2State, self.__LED3State,
                          source, self.___line)

  def _bindToVisit(self, Visit):
    self.__Visit = Visit

  def __repr__(self):
    return '< Nosepoke to %5s door (at %s) >' % \
           (self.Door, getTimeString(self.Start))


class LogEntry(BaseNode, SideAware):
  __slots__ = ('DateTime', 'Category', 'Type',
                'Cage', 'Corner', 'Side', 'Notes',
                '_source', '_line')

  def __init__(self, DateTime, Category, Type,
                     Cage, Corner, Side, Notes, _source, _line):
    self.__DateTime = DateTime
    self.__Category = Category
    self.__Type = Type
    self.__Cage = Cage
    self.__Corner = Corner
    self.__Side = Side
    self.__Notes = Notes
    self.___source = _source
    self.___line = _line

  def clone(self, sourceManager, cageManager):
    cage, corner, side = None, None, None
    if self.__Cage is not None:
      cage = cageManager[self.__Cage]

      if self.__Corner is not None:
        corner = cage[self.__Corner]

        if self.__Side is not None:
          side = corner[self.__Side]

    return LogEntry(self.__DateTime,
                    self.__Category,
                    self.__Type,
                    cage,
                    corner,
                    side,
                    self.__Notes,
                    sourceManager[self.___source],
                    self.___line)

  def __repr__(self):
    return '< Log %s, %s (at %s) >' % \
           (self.__Category, self.__Type,
            getTimeString(self.__DateTime))


class EnvironmentalConditions(BaseNode):
  __slots__ = ('DateTime', 'Temperature', 'Illumination', 'Cage',
                '_source', '_line')

  def __init__(self, DateTime, Temperature, Illumination, Cage,
               _source, _line):
    self.__DateTime = DateTime
    self.__Temperature = Temperature
    self.__Illumination = Illumination
    self.__Cage = Cage
    self.___source = _source
    self.___line = _line

  def clone(self, sourceManager, cageManager):
    return self.__class__(self.__DateTime,
                          self.__Temperature,
                          self.__Illumination,
                          cageManager[self.__Cage],
                          sourceManager[self.___source],
                          self.___line)

  def __repr__(self):
    return '< Illumination: %3d, Temperature: %4.1f (at %s) >' % \
           (self.__Illumination, self.__Temperature,
            getTimeString(self.__DateTime))


class HardwareEvent(BaseNode, SideAware):
  __slots__ = ()


class NamedInt(int):
  #__slots__ = ('__text',)

  def __new__(cls, value, text='_Unknown'):
    obj = int.__new__(cls, value)
    obj.__text = text
    return obj

  def __str__(self):
    return self.__text

  def __repr__(self):
    return '%s(%d, %s)' % (self.__class__.__name__, int(self), repr(self.__text))

  def __setattr__(self, key, value):
    if key == '_NamedInt__text':
      self.__dict__[key] = value

    else:
      raise AttributeError(key)


class KnownHardwareEvent(HardwareEvent):
  __slots__ = ('DateTime', 'Cage', 'Corner', 'Side', 'State',
               '_source', '_line')

  def __init__(self, DateTime, Cage, Corner, Side, State, _source, _line):
    self.__DateTime = DateTime
    self.__Cage = Cage
    self.__Corner = Corner
    self.__Side = Side
    self.__State = State
    self.___source = _source
    self.___line = _line

  def clone(self, sourceManager, cageManager):
    corner, side = self.__Corner, self.__Side
    cage = cageManager[self.__Cage]
    if corner is not None:
      corner = cage[corner]
      if side is not None:
        side = corner[side]

    return self.__class__(self.__DateTime,
                          cage, corner, side,
                          self.__State,
                          sourceManager[self.___source],
                          self.___line)


class AirHardwareEvent(KnownHardwareEvent):
  Type = NamedInt(0, 'Air')
  __slots__ = ()

  def __repr__(self):
    return '< AirEvent: %d (at %s) >' % \
           (self.State, getTimeString(self.DateTime))


class DoorHardwareEvent(KnownHardwareEvent):
  Type = NamedInt(1, 'Door')
  __slots__ = ()

  def __repr__(self):
    return '< DoorEvent: %d (at %s) >' % \
           (self.State, getTimeString(self.DateTime))


class LedHardwareEvent(KnownHardwareEvent):
  Type = NamedInt(2, 'LED')
  __slots__ = ()

  def __repr__(self):
    return '< LedEvent: %d (at %s) >' % \
           (self.State, getTimeString(self.DateTime))


class UnknownHardwareEvent(HardwareEvent):
  __slots__ = ('DateTime', 'Type', 'Cage', 'Corner', 'Side', 'State',
               '_source', '_line')

  def __init__(self, DateTime, Type, Cage, Corner, Side, State,
               _source, _line):
    self.__DateTime = DateTime
    self.__Type = Type
    self.__Cage = Cage
    self.__Corner = Corner
    self.__Side = Side
    self.__State = State
    self.___source = _source
    self.___line = _line

  def clone(self, sourceManager, cageManager):
    corner, side = self.__Corner, self.__Side
    cage = cageManager[self.__Cage]
    if corner is not None:
      corner = cage[corner]
      if side is not None:
        side = corner[side]

    return UnknownHardwareEvent(self.__DateTime,
                                self.__Type,
                                cage, corner, side,
                                self.__State,
                                sourceManager[self.___source],
                                self.___line)

  def __repr__(self):
    return '< UnknownHardwareEvent(%d): %d (at %s) >' % \
           (self.Type, self.State, getTimeString(self.DateTime))


# TODO
class DataNode(object):
  _baseAttrs = []
  _keys = []

  def __init__(self, **kwargs):
    self.__dict__.update(kwargs)

  @classmethod
  def fromDict(cls, d):
    return cls(**d)

  def merge(self, **kwargs):
    updated = {}
    for k in self._keys:
      v = kwargs.pop(k, None)
      if v is not None:
        current = self.__dict__.get(v)
        if current is None:
          updated[k] = v

        elif v != current:
          raise ValueError("%s conflict: %s != %s." % (k, current, v))

    for k, v in kwargs.items():
      if v is not None:
        current = self.__dict__.get(k)
        if current is None:
          updated[k] = v

        elif current != v:
          warnings.warn("%s conflict: %s != %s. Update ignored." %\
                        (k, current, v))

    self.__dict__.update(updated)
    return updated


  def __getitem__(self, key):
    return self.__dict__[key]

  def get(self, key, default=None):
    return self.__dict__(key, default)

  def __setitem__(self, key, value):
    return self.__dict__.__setitem__(key, value)

  def __delitem__(self, key):
    return self.__dict__.__delitem__(key)

  def __contains__(self, item):
    return item in self.__dict__

  def keys(self):
    return self.__dict__.keys()

  def pop(self, key, *args, **kwargs):
    return self.__dict__.pop(key, *args, **kwargs)

  def update(self, *args, **kwargs):
    return self.__dict__.update(*args, **kwargs)

  def copy(self):
    return self.__class__(**self.__dict__)

  def _del_(self):
    self.__dict__.clear()

  def select(self, query):
    return map(self.__dict__.get, query)


class Session(DataNode):
  _baseAttrs = ['Start', 'End']

  def __init__(self, Start, End, **kwargs):
    DataNode.__init__(self, **kwargs)
    self.Start = toDt(Start)
    self.End = toDt(End)


# TODO
class Group(DataNode):
  _baseAttrs = ['Name', 'Animals']
  _keys = ['Name']

  def __init__(self, Name, Animals=[], Notes=None, Module=None, **kwargs):
    DataNode.__init__(self, **kwargs)
    self.Name = unicode(Name)
    self.Animals = []
    for animal in Animals:
      self.addMember(animal)

  def __str__(self):
    return str(self.Name)

  def __unicode__(self):
    return unicode(self.Name)

  def addMember(self, animal):
    aName = unicode(animal)
    for a in self.Animals:
      if aName == unicode(a):
        return

    self.Animals.append(animal) #XXX might cause a serious conflict unless some animal manager is provided

  def delMember(self, animal):
    aName = unicode(animal)
    self.Animals = [a for a in self.Animals if unicode(a) != aName]

  def merge(self, Animals=[], **kwargs):
    updated = DataNode.merge(self, **kwargs)
    for animal in Animals:
      self.addMember(animal)
