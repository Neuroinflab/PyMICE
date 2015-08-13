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

import operator
from itertools import imap
import collections
from _Tools import toDt

def getTimeString(time):
  return time.strftime('%Y-%m-%d %H:%M:%S') + \
         ('%.3f' % (time.microsecond / 1000000.))[1:5]


def makePrivateSlots(attributes):
  return tuple('__' + s for s in attributes)


class BaseNode(object):
  __slots__ = ()

  def _del_(self):
    privatePrefix = '_' + self.__class__.__name__
    for attr in self.__slots__:
      try:
        delattr(self, privatePrefix + attr)

      except AttributeError:
        pass

  @classmethod
  def _finishClassDefinition(cls):
    cls._makeReadOnlyAttributes()

  @classmethod
  def _makeReadOnlyAttributes(cls):
    privatePrefix = '_%s__' % cls.__name__
    for attr in cls.attributes:
      setattr(cls, attr, property(operator.attrgetter(privatePrefix + attr)))

  @classmethod
  def _finishSubclassesDefinitions(cls):
    for subClass in cls.__subclasses__():
      subClass._finishClassDefinition()


class DurationAware(object):
  __slots__ = ()
  @property
  def Duration(self):
    return self.End - self.Start


class SideAware(object):
  __slots__ = ()
  @property
  def Door(self):
    side = self.Side
    if side is not None:
      return 'left' if side % 2 == 1 else 'right'


class Animal(BaseNode):
  class DifferentMouse(ValueError):
    pass

  attributes = ('Name', 'Tag', 'Sex', 'Notes')
  __slots__ = makePrivateSlots(attributes)

  def __init__(self, Name, Tag, Sex=None, Notes=None):
    self.__Name = Name
    self.__Tag = Tag
    self.__Sex = Sex
    self.__Notes = Notes if isinstance(Notes, frozenset) else frozenset() if Notes is None else frozenset({unicode(Notes)})

  @classmethod
  def fromRow(cls, Name, Tag, Sex=None, Notes=None):
    return cls(unicode(Name),
               frozenset({long(Tag)}),
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

  def __str__(self):
    return self.__Name.encode('utf-8')

  def __unicode__(self):
    return self.__Name

  def __repr__(self):
    result = '< Animal %s (' % self.Name
    if self.__Sex is not None:
      result += '%s; ' % self.Sex

    result += 'Tag: ' if len(self.__Tag) == 1 else 'Tags: '
    result += ', '.join(str(t) for t in self.__Tag)
    return result + ') >'

  def merge(self, other):
    if self != other:
      raise self.DifferentMouse

    if self.__Sex is None:
      self.__Sex = other.__Sex

    self.__Notes = self.__Notes | other.__Notes
    self.__Tag = self.__Tag | other.__Tag


class Visit(BaseNode, DurationAware):
  attributes = ('Start', 'Corner', 'Animal', 'End', 'Module', 'Cage',
                'CornerCondition', 'PlaceError',
                'AntennaNumber', 'AntennaDuration',
                'PresenceNumber', 'PresenceDuration',
                'VisitSolution',
                '_source', '_line',
                'Nosepokes')
  __slots__ = makePrivateSlots(attributes)

  def __init__(self, Start, Corner, Animal, End=None, Module=None, Cage=None,
               CornerCondition=None, PlaceError=None,
               AntennaNumber=None, AntennaDuration=None,
               PresenceNumber=None, PresenceDuration=None,
               VisitSolution=None,
               _source=None, _line=None,
               Nosepokes=None):
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

  def clone(self, cageManager, animalManager, sourceManager):
    sideManager = cageManager.getSideManager(self.__Cage, self.__Corner)
    nosepokes = tuple(n.clone(sideManager, sourceManager) for n in self.__Nosepokes)
    source = sourceManager.get(self.___source)
    animal = animalManager.get(self.__Animal)
    cage, corner = cageManager.getCageCorner(self.__Cage, self.__Corner)
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


  @classmethod
  def _finishClassDefinition(cls):
    cls._makeReadOnlyAttributes()
    cls._makeNosepokeAggregativeProperties()

  @classmethod
  def _makeNosepokeAggregativeProperties(cls):
    for propertyAttr in [('NosepokeDuration', 'Duration'),
                         'LickNumber',
                         'LickDuration',
                         'LickContactTime',
                        ]:
      cls.__setNosepokeAggregativeProperty(propertyAttr)

  @classmethod
  def __setNosepokeAggregativeProperty(cls, arg):
    propName, attrName = (arg, arg) if isinstance(arg, basestring) else arg
    setattr(cls, propName, cls.__makeNosepokeAggregativeProperty(attrName))

  @staticmethod
  def __makeNosepokeAggregativeProperty(attr):
    npAttrGetter = operator.attrgetter(attr)
    def propertyGetter(self):
      nosepokes = self._Visit__Nosepokes
      if nosepokes is not None:
        return sum(imap(npAttrGetter, nosepokes))

    return property(propertyGetter)

  def __repr__(self):
    return '< Visit of "%s" to corner #%d of cage #%d (at %s) >' % \
           (self.__Animal, self.__Corner, self.__Cage,
            getTimeString(self.__Start))


class Nosepoke(BaseNode, SideAware, DurationAware):
  attributes = ('Start', 'End', 'Side',
                'LickNumber', 'LickContactTime', 'LickDuration',
                'SideCondition', 'SideError', 'TimeError', 'ConditionError',
                'AirState', 'DoorState', 'LED1State', 'LED2State', 'LED3State',
                '_source', '_line',
                'Visit',
                )
  __slots__ = makePrivateSlots(attributes)
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

  def clone(self, sideManager, sourceManager):
    side = sideManager.get(self.__Side)
    source = sourceManager.get(self.___source)
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


BaseNode._finishSubclassesDefinitions()


# TODO

class DataNode(object):
  __slots__ = []
  _baseAttrs = []
  _keys = []

  def __init__(self, **kwargs):
    for k, v in kwargs.items():
      self.__setattr__(k, v)

      #self.__dict__.update(kwargs)

  @classmethod
  def fromDict(cls, d):
    return cls(**d)

  # @classmethod #XXX
  # def fromKwargs(cls, _mapping={}, **kwargs):
  #   updates = [(k, f(kwargs[k])) for k, f in _mapping.items() if k in kwargs]
  #   kwargs.update(updates)
  #   return cls(**kwargs)
  #
  # def merge(self, **kwargs):
  #   updated = {}
  #   for k in self._keys:
  #     v = kwargs.pop(k, None)
  #     if v is not None:
  #       current = self.__dict__.get(v)
  #       if current is None:
  #         updated[k] = v
  #
  #       elif v != current:
  #         raise ValueError("%s conflict: %s != %s." % (k, current, v))
  #
  #   for k, v in kwargs.items():
  #     if v is not None:
  #       current = self.__dict__.get(k)
  #       if current is None:
  #         updated[k] = v
  #
  #       elif current != v:
  #         warnings.warn("%s conflict: %s != %s. Update ignored." %\
  #                       (k, current, v))
  #
  #   self.__dict__.update(updated)
  #   return updated
  #
  #
  def __getitem__(self, key):
    try:
      return self.__getattribute__(key)

    except AttributeError:
      raise KeyError(key)
  #
  def get(self, key, default=None):
    try:
      return self.__getattribute__(key)

    except AttributeError:
      return default

  #   #return self.__dict__.get(key, default)
  #   # not very Pythonic but fast
  #   return self.__dict__[key] if key in self.__dict__ else default
  #
  # def __setitem__(self, key, value):
  #   return self.__setattr__(key, value)
  #   #return self.__dict__.__setitem__(key, value)
  #
  # def __delitem__(self, key):
  #   return self.__delattr__(key)
  #   #return self.__dict__.__delitem__(key)
  #
  # def __contains__(self, item):
  #   return hasattr(self, item)
  #   #return item in self.__dict__
  #
  def keys(self):
    keys = []
    for key in self.__slots__:
      try:
        self.__getattribute__(key)

      except AttributeError:
        pass

      else:
        keys.append(key)

    return keys

  #
  def pop(self, key, *args, **kwargs):
    try:
      value = self.__getattribute__(key)

    except AttributeError:
      raise KeyError(key)

    self.__delattr__(key)
    return value

    #   return self.__dict__.pop(key, *args, **kwargs)
    #
    # def update(self, *args, **kwargs):
    #   return self.__dict__.update(*args, **kwargs)
    #
    # def copy(self):
    #   return self.__class__(**self.__dict__)
    #
    # def _del_(self):
    #   self.__dict__.clear()
    #
    # def select(self, query):
    #   return map(self.__dict__.get, query)




class Session(DataNode):
  _baseAttrs = ['Start', 'End']

  def __init__(self, Start, End, **kwargs):
    DataNode.__init__(self, **kwargs)
    self.Start = toDt(Start)
    self.End = toDt(End)


# TODO
# class LogEntry(SideAware):
#   _baseAttrs = ['DateTime', 'Category', 'Type',
#                 'Cage', 'Corner', 'Side', 'Notes']
#
#   def __init__(self, DateTime, Category=None, Type=None, Cage=None,
#                Corner=None, Side=None, Notes=None, **kwargs):
#     DataNode.__init__(self, **kwargs)
#     self.DateTime = toDt(DateTime)
#     self.Category = unicode(Category) if Category is not None else None
#     self.Type = unicode(Type) if Type is not None else None
#     self.Cage = int(Cage) if Cage is not None else None
#     self.Corner = int(Corner) if Corner is not None else None
#     self.Side = int(Side) if Side is not None else None
#     self.Notes = unicode(Notes) if Notes is not None else None
#
#   def __repr__(self):
#     return '< Log %s, %s (at %s) >' % \
#            (self.Category, self.Type, getTimeString(self.DateTime))
#
#
# class EnvironmentalConditions(DataNode):
#   _baseAttrs = ['DateTime', 'Temperature', 'Illumination', 'Cage']
#
#   def __init__(self, DateTime, Temperature=None, Illumination=None, Cage=None,
#                **kwargs):
#     DataNode.__init__(self, **kwargs)
#     self.DateTime = toDt(DateTime)
#     self.Temperature = float(Temperature) if Temperature is not None else None
#     self.Illumination = int(Illumination) if Illumination is not None else None
#     self.Cage = int(Cage) if Cage is not None else None
#
#   def __repr__(self):
#     return '< Illumination: %d, Temperature: %f (at %s) >' % \
#            (self.Illumination, self.Temperature, getTimeString(self.DateTime))
#
#
# class HardwareEvent(SideAware):
#   _baseAttrs = ['DateTime', 'Type', 'Cage', 'Corner', 'Side', 'State']
#   __typeMapping = {0: 'Air',
#                    1: 'Door',
#                    2: 'LED',
#                    }
#
#   def __init__(self, DateTime, Type=None, Cage=None, Corner=None, Side=None, State=None,
#                **kwargs):
#     DataNode.__init__(self, **kwargs)
#     self.DateTime = toDt(DateTime)
#     self.Type = self.__typeMapping[int(Type)] if Type is not None else None
#     self.Cage = int(Cage) if Cage is not None else None
#     self.Corner = int(Corner) if Corner is not None else None
#     self.Side = int(Side) if Side is not None else None
#     self.State = int(State) if State is not None else None
#
#   def __repr__(self):
#     side = '' if self.Side is None else ', %5s side' % self.Door
#     return '< HardwareEvent %s: %d in cage #%d, corner #%d%s (at %s) >' % \
#            (self.Type, self.State, self.Cage, self.Corner, side,
#             getTimeString(self.DateTime))




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


# OMG!!!
class ICCageManager(object):
  def __init__(self):
    self.__cages = {}

  #def add(cage):
  #  if int(cage) not in self.__cages:
  #    self.__cages[cage] = ICCage(cage)

  #  return self.get(cage)

  def get(cage, corner=None, side=None):
    try:
      cage = self.__cages[int(cage)]

    except KeyError:
      cage = ICCage(cage)
      self.__cages[int(cage)] = cage

    if corner is not None:
      corner = int(corner)
      if side is not None:
        return cage.corners[corner].sides[str(side)]

      return cage.corners[corner]

    if side is not None:
      return cage.sides[int(side)]

    return cage

  def __del__(self):
    for cage in self.__cages.values():
      cage._del_()

    del self.__cages


class ICCage(int):
  def __init__(self, cage):
    int.__init__(self, cage)
    self.corners = dict((i, ICCornerInt(self, i)) for i in xrange(1,5))
    self.sides = dict((int(side), side) for corner in self.corners.values()\
                                        for side in self.side.values())

  def _del_(self):
    for corner in self.corners.values():
      corner._del_()

    del self.corners
    del self.sides

  def __repr__(self):
    return "Cage #%d" % self


class ICCorner(int):
  def __init__(self, cage, corner):
    int.__init__(self, corner)
    self.cage = cage

    self.sides = dict((side, ICSide(self * 2 - 1 + i, self)) \
                      for (i, side) in enumerate(['left', 'right']))

  def _del_(self):
    for side in self.sides.values():
      side._del_()

    del self.sides
    del self.cage

  def __repr__(self):
    return "Corner #%d of cage #%d" % (self, self.cage)


class ICSide(int):
  def __init__(self, side, corner):
    int.__init__(self, side)
    self.corner = corner

  def _del_(self):
    del self.corner

  def __str__(self):
    return 'left' if self % 2 == 1 else 'right'

  def __unicode__(self):
    return u'left' if self % 2 == 1 else u'right'

  def __repr__(self):
    return "%s side of corner #%d" % (str(self), (self + 1) / 2) 


