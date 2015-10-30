import sys
from datetime import timedelta

if sys.version_info < (3, 0):
  from itertools import imap

else:
  imap = map
  basestring = str

from operator import attrgetter



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
    propName, attrName = (arg, arg) if isinstance(arg, basestring) else arg
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