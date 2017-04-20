#!/usr/bin/env python
# encoding: utf-8
###############################################################################
#                                                                             #
#    PyMICE library                                                           #
#                                                                             #
#    Copyright (C) 2012-2017 Jakub M. Dzik a.k.a. Kowalski, S. Łęski          #
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
from datetime import timedelta

if sys.version_info < (3, 0):
  from itertools import imap

else:
  imap = map

from operator import attrgetter

from ._Tools import isString

def makePrivateSlots(attributes, name):
  prefix = '_%s__' % name
  return tuple(prefix + s for s in attributes)


class BaseNodeMetaclass(type):
  def __new__(mcl, name, bases, attrs):
    attributes = attrs['__slots__']
    slots = makePrivateSlots(attributes, name)
    attrs['__slots__'] = slots
    attrs.update(zip(attributes,
                     (property(attrgetter(s)) for s in slots)))

    return type.__new__(mcl, name, bases, attrs)


def BaseNode_del_(self):
  for cls in self.__class__.__mro__:
    if not hasattr(cls, '__slots__'):
      continue

    for attr in cls.__slots__:
      try:
        delattr(self, attr)

      except AttributeError:
        pass


class VisitMetaclass(BaseNodeMetaclass):
  __npSummaryProperties = [(('NosepokeDuration', 'Duration'), timedelta(0)),
                           ('LickNumber', 0),
                           ('LickDuration', timedelta(0)),
                           ('LickContactTime', timedelta(0)),
                           ]
  def __new__(cls, name, bases, attrs):
    cls.__addNosepokeSummaryPropertiesToDict(attrs)
    return BaseNodeMetaclass.__new__(cls, name, bases, attrs)

  @classmethod
  def __addNosepokeSummaryPropertiesToDict(cls, dict):
    dict.update(cls.__makeNosepokeSummaryPropertyPair(*propertyAttr) \
                for propertyAttr in cls.__npSummaryProperties)

  @classmethod
  def __makeNosepokeSummaryPropertyPair(cls, arg, start):
    propName, attrName = (arg, arg) if isString(arg) else arg
    return propName, cls.__makeNosepokeAggregativeProperty(attrName, start)

  @staticmethod
  def __makeNosepokeAggregativeProperty(attr, start):
    npAttrGetter = attrgetter(attr)
    def propertyGetter(self):
      nosepokes = self._Visit__Nosepokes
      if nosepokes is not None:
        return sum(imap(npAttrGetter, nosepokes), start)

    return property(propertyGetter)


class DurationAware(object):
  class DurationCannotBeCalculatedError(AttributeError):
    pass

  __slots__ = ()
  @property
  def Duration(self):
    try:
      return self.End - self.Start

    except TypeError:
      raise self.DurationCannotBeCalculatedError


def getTimeString(time):
  return time.strftime('%Y-%m-%d %H:%M:%S') + \
         ('%.3f' % (time.microsecond / 1000000.))[1:5]