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

import warnings
from _Tools import toDt 

class DataNode(object):
  _baseAttrs = []
  _keys = []
  _convert = {}

  def __init__(self, **kwargs):
    self.__dict__.update(kwargs)
    #self._attrs = set(self._baseAttrs + kwargs.keys())
    #for k, v in kwargs.items():
    #  setattr(self, k, v)

  @classmethod
  def fromDict(cls, d):
    return cls(**d)

  @classmethod #XXX
  def fromKwargs(cls, _mapping={}, **kwargs):
    updates = [(k, f(kwargs[k])) for k, f in _mapping.items() if k in kwargs]
    kwargs.update(updates)
    return cls(**kwargs)

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
    return self.__dict__.__getitem__(key)

  def get(self, key, default=None):
    #return self.__dict__.get(key, default)
    # not very Pythonic but fast
    return self.__dict__[key] if key in self.__dict__ else default

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

  #def __setitem__(self, key, value):
  #  self._attrs.add(key)
  #  setattr(self, key, value)

  #def keys(self):
  #  return list(self._attrs)

  #def items(self):
  #  return [(k, getattr(self, k) for k in self._attrs]

  def select(self, query):
    return map(self.__dict__.get, query)


class SessionNode(DataNode):
  _baseAttrs = DataNode._baseAttrs + ['Start', 'End']

  def __init__(self, Start, End, **kwargs):
    DataNode.__init__(self, **kwargs)
    self.Start = toDt(Start)
    self.End = toDt(End)


# TODO
class LogNode(DataNode):
  _baseAttrs = DataNode._baseAttrs + ['DateTime', 'Category', 'Type', 'Cage',
                                      'Corner', 'Side', 'Notes']

  def __init__(self, DateTime, Category=None, Type=None, Cage=None,
               Corner=None, Side=None, Notes=None, **kwargs):
    DataNode.__init__(self, **kwargs)
    self.DateTime = toDt(DateTime)
    self.Category = unicode(Category) if Category is not None else None
    self.Type = unicode(Type) if Type is not None else None
    self.Cage = int(Cage) if Cage is not None else None
    self.Corner = int(Corner) if Corner is not None else None
    self.Side = int(Side) if Side is not None else None
    self.Notes = unicode(Notes) if Notes is not None else None


class EnvironmentNode(DataNode):
  _baseAttrs = DataNode._baseAttrs + ['DateTime', 'Temperature',
                                      'Illumination', 'Cage']

  def __init__(self, DateTime, Temperature=None, Illumination=None, Cage=None,
               **kwargs):
    DataNode.__init__(self, **kwargs)
    self.DateTime = toDt(DateTime)
    self.Temperature = float(Temperature) if Temperature is not None else None
    self.Illumination = int(Illumination) if Illumination is not None else None
    self.Cage = int(Cage) if Cage is not None else None


class HardwareEventNode(DataNode):
  _baseAttrs = DataNode._baseAttrs + ['DateTime', 'Type',
                                      'Cage', 'Corner', 'Side', 'State']
  __typeMapping = {0: 'Air',
                   1: 'Door',
                   2: 'LED',
                   }

  def __init__(self, DateTime, Type=None, Cage=None, Corner=None, Side=None, State=None,
               **kwargs):
    DataNode.__init__(self, **kwargs)
    self.DateTime = toDt(DateTime)
    self.Type = self.__typeMapping[int(Type)] if Type is not None else None
    self.Cage = int(Cage) if Cage is not None else None
    self.Corner = int(Corner) if Corner is not None else None
    self.Side = int(Side) if Side is not None else None
    self.State = int(State) if State is not None else None


class AnimalNode(DataNode):
  _baseAttrs = DataNode._baseAttrs + ['Name', 'Tag', 'Sex', 'Notes']
  _keys = ['Name', 'Sex']

  def __init__(self, Name, Tag, Sex=None, Notes=None, **kwargs):
    DataNode.__init__(self, **kwargs)
    self.Name = unicode(Name)
    self.Tag = (set(Tag) if isinstance(Tag, set) else long(Tag))\
               if Tag is not None\
               else None
    self.Sex = unicode(Sex) if Sex is not None else None
    self.Notes = unicode(Notes) if Notes is not None else None

  def __repr__(self):
    result = "Animal %s" % self.Name

    if self.Sex is not None or self.Tag is not None:
      result += "("
      if self.Sex is not None:
        result += self.Sex

      if self.Sex is not None and self.Tag is not None:
        result += "; "

      if self.Tag is not None:
        if isinstance(self.Tag, set):
          result += "Tags: " + (', '.join(map(str, sorted(self.Tag))))

        else:
          result += "Tag: %d" % self.Tag

      result += ")"

    return result

  def __str__(self):
    return str(self.Name)

  def __unicode__(self):
    return unicode(self.Name)

  def __eq__(self, other):
    if self.Name != other['Name']:
      return False

    if self.Sex == other['Sex'] or self.Sex is None or other['Sex'] is None:
      return True

    return NotImplemented

  def __ne__(self, other):
    if self.Name != other['Name']:
      return True

    if self.Sex == other['Sex'] or self.Sex is None or other['Sex'] is None:
      return False

    return NotImplemented

  def merge(self, Tag=None, **kwargs):
    updated = DataNode.merge(self, **kwargs)
    if Tag is not None and self.Tag != Tag:
      if self.Tag is None:
        self.Tag = set(Tag) if isinstance(Tag, set) else Tag

      else:
        if not isinstance(self.Tag, set):
          self.Tag = set([self.Tag])

        if isinstance(Tag, set):
          self.Tag.update(Tag)

        else:
          self.Tag.add(Tag)


class VisitNode(DataNode):
  _baseAttrs = DataNode._baseAttrs + ['Start', 'End', 'ModuleName', 'Cage',
               'Corner', 'CornerCondition', 'PlaceError', 'AntennaNumber',
               'AntennaDuration', 'PresenceNumber', 'PresenceDuration',
               '_vid', 'VisitSolution']

  def __init__(self, Start, Corner, End=None, ModuleName=None, Cage=None,
               CornerCondition=None, PlaceError=None, AntennaNumber=None,
               AntennaDuration=None, PresenceNumber=None, PresenceDuration=None,
               VisitSolution=None, **kwargs):
    super(VisitNode, self).__init__(**kwargs)
    self.Start = toDt(Start)
    self.Corner = int(Corner)
    self.End = toDt(End)
    self.ModuleName = unicode(ModuleName) if ModuleName is not None else None
    self.Cage = int(Cage) if Cage is not None else None
    self.CornerCondition = float(CornerCondition) if CornerCondition is not None else None
    self.PlaceError = float(PlaceError) if PlaceError is not None else None
    self.AntennaNumber = int(AntennaNumber) if AntennaNumber is not None else None
    self.AntennaDuration = float(AntennaDuration) if AntennaDuration is not None else None
    self.PresenceNumber = int(PresenceNumber) if PresenceNumber is not None else None
    self.PresenceDuration = float(PresenceDuration) if PresenceDuration is not None else None
    self.VisitSolution = int(VisitSolution) if VisitSolution is not None else None


  # derivatives
  @property
  def Duration(self):
    return self.End - self.Start

  @property
  def NosepokeNumber(self):
    if 'Nosepokes' in self.__dict__ and self.__dict__['Nosepokes'] is not None:
      return len(self.__dict__['Nosepokes'])

    if 'NosepokeNumber' in self.__dict__:
      return self.__dict__['NosepokeNumber']

  @NosepokeNumber.setter
  def NosepokeNumber(self, value):
    self.__dict__['NosepokeNumber'] = int(value) if value is not None else None

  @property
  def NosepokeDuration(self):
    if 'Nosepokes' in self.__dict__ and self.__dict__['Nosepokes'] is not None:
      return float(sum(n.Duration for n in self.__dict__['Nosepokes']))

    if 'NosepokeDuration' in self.__dict__:
      return self.__dict__['NosepokeDuration']

  @NosepokeDuration.setter
  def NosepokeDuration(self, value):
    self.__dict__['NosepokeDuration'] = float(value) if value is not None else None

  @property
  def LickNumber(self):
    if 'Nosepokes' in self.__dict__ and self.__dict__['Nosepokes'] is not None:
      return sum(n.LickNumber for n in self.__dict__['Nosepokes'])

    if 'LickNumber' in self.__dict__:
      return self.__dict__['LickNumber']

  @LickNumber.setter
  def LickNumber(self, value):
    self.__dict__['LickNumber'] = int(value) if value is not None else None

  @property
  def LickDuration(self):
    if 'Nosepokes' in self.__dict__ and self.__dict__['Nosepokes'] is not None:
      return float(sum(n.LickDuration for n in self.__dict__['Nosepokes']))

    if 'LickDuration' in self.__dict__:
      return self.__dict__['LickDuration']

  @LickDuration.setter
  def LickDuration(self, value):
    self.__dict__['LickDuration'] = float(value) if value is not None else None

  @property
  def LickContactTime(self):
    if 'Nosepokes' in self.__dict__ and self.__dict__['Nosepokes'] is not None:
      return float(sum(n.LickContactTime for n in self.__dict__['Nosepokes']))

    if 'LickContactTime' in self.__dict__:
      return self.__dict__['LickContactTime']

  @LickContactTime.setter
  def LickContactTime(self, value):
    self.__dict__['LickContactTime'] = float(value) if value is not None else None

  def _del_(self):
    if self.Nosepokes:
      for npNode in self.Nosepokes:
        npNode._del_()

    super(VisitNode, self)._del_()


class NosepokeNode(DataNode):
  _baseAttrs = DataNode._baseAttrs + ['Start', 'End', 'Side', 'LickNumber',
                                      'LickContactTime', 'LickDuration',
                                      'SideCondition', 'SideError', 'TimeError',
                                      'ConditionError', 'AirState', 'DoorState',
                                      'LED1State', 'LED2State', 'LED3State',]
  _convert = dict(DataNode._convert) # TODO ?

  def __init__(self, Start=None, End=None, Side=None, LickNumber=None,
               LickContactTime=None, LickDuration=None,
               SideCondition=None, SideError=None, TimeError=None,
               ConditionError=None, AirState=None, DoorState=None,
               LED1State=None, LED2State=None, LED3State=None, **kwargs): # TODO
    DataNode.__init__(self, **kwargs)
    self.Start = toDt(Start)
    self.End = toDt(End)
    self.Side = int(Side) if Side is not None else None
    self.LickNumber = int(LickNumber) if LickNumber is not None else None
    self.LickContactTime = float(LickContactTime) if LickContactTime is not None else None
    self.LickDuration = float(LickDuration) if LickDuration is not None else None
    self.SideCondition = float(SideCondition) if SideCondition is not None else None 
    self.SideError =  float(SideError) if SideError is not None else None
    self.TimeError = float(TimeError) if TimeError is not None else None
    self.ConditionError = float(ConditionError) if ConditionError is not None else None
    self.AirState = int(AirState) if AirState is not None else None
    self.DoorState = int(DoorState) if DoorState is not None else None
    self.LED1State = int(LED1State) if LED1State is not None else None
    self.LED2State = int(LED2State) if LED2State is not None else None
    self.LED3State = int(LED3State) if LED3State is not None else None

  @property
  def Duration(self):
    return self.End - self.Start

  @property
  def Door(self):
    return 'left' if self.Side % 2 == 1 else 'right'


class GroupNode(DataNode):
  _baseAttrs = DataNode._baseAttrs + ['Name', 'Animals']
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
