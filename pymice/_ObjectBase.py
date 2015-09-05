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

import numpy as np
from operator import attrgetter
from collections import Sequence

class ObjectBase(object):
  """
  A base class for efficient object filtering.

  >>> ob = ObjectBase()
  >>> ob.get()
  []

  >>> len(ob)
  0

  >>> ob.put([ClassA(1, 4)])
  >>> ob.get()
  [ClassA(a=1, b=4)]

  >>> len(ob)
  1

  >>> ob.put([ClassA(2, 2)])
  >>> ob.get()
  [ClassA(a=1, b=4), ClassA(a=2, b=2)]

  >>> ob.put([ClassA(2, 2), ClassB(0, 0)])
  >>> ob.get()
  [ClassA(a=1, b=4), ClassA(a=2, b=2), ClassA(a=2, b=2), ClassB(c=0, d=0)]

  >>> len(ob)
  4

  >>> tmp = ob.get()
  >>> tmp.append(1)
  >>> ob.get()
  [ClassA(a=1, b=4), ClassA(a=2, b=2), ClassA(a=2, b=2), ClassB(c=0, d=0)]

  >>> ob = ObjectBase()
  >>> ob.put([ClassA(1, 4), ClassA(2, 2), ClassA(2, 2)])
  >>> ob.get()
  [ClassA(a=1, b=4), ClassA(a=2, b=2), ClassA(a=2, b=2)]

  >>> tmp = ob.get()
  >>> tmp[2].b = 42
  >>> ob.get()
  [ClassA(a=1, b=4), ClassA(a=2, b=2), ClassA(a=2, b=42)]

  >>> tmp = []
  >>> ob = ObjectBase()
  >>> ob.put(tmp)
  >>> ob.put([ClassA(2, 2), ClassB(0, 0)])
  >>> tmp
  []

  >>> ob = ObjectBase()
  >>> ob.put([ClassA(1, 4)])
  >>> ob.get({'a': lambda x: x == 1})
  [ClassA(a=1, b=4)]

  >>> ob.get({'a': lambda x: x != 1})
  []

  >>> ob.put([ClassA(2, 2), ClassA(1, 2)])
  >>> ob.get({'a': lambda x: x != 1})
  [ClassA(a=2, b=2)]

  >>> ob.get({'a': lambda x: x == 1,
  ...         'b': lambda x: x == 2})
  [ClassA(a=1, b=2)]

  >>> ob.get({'a': lambda x: x == 2,
  ...         'b': lambda x: x == 4})
  []

  >>> ob.get({})
  [ClassA(a=1, b=4), ClassA(a=2, b=2), ClassA(a=1, b=2)]

  >>> ob = ObjectBase()
  >>> ob.get({'a': lambda x: x == 1,
  ...         'b': lambda x: x == 2})
  []

  >>> ob = ObjectBase()
  >>> ob.put([ClassA(ClassB(1, 2), 1), ClassA(ClassB(2, 3), 2),
  ...         ClassA(ClassB(4, 3), 3)])
  >>> ob.get({'b': lambda x: (x == 1) + (x == 3)})
  [ClassA(a=ClassB(c=1, d=2), b=1), ClassA(a=ClassB(c=4, d=3), b=3)]

  >>> ob.get({'a.d': lambda x: x == 3})
  [ClassA(a=ClassB(c=2, d=3), b=2), ClassA(a=ClassB(c=4, d=3), b=3)]

  >>> ob = ObjectBase({'a': lambda x: x.d - x.c})
  >>> ob.put([ClassA(ClassB(1, 2), 1), ClassA(ClassB(2, 3), 2),
  ...         ClassA(ClassB(4, 3), 3)])
  >>> ob.get({'a': lambda x: x == 1})
  [ClassA(a=ClassB(c=1, d=2), b=1), ClassA(a=ClassB(c=2, d=3), b=2)]

  >>> ob.get({'a': (1,)})
  [ClassA(a=ClassB(c=1, d=2), b=1), ClassA(a=ClassB(c=2, d=3), b=2)]

  >>> ob.get({'a': ()})
  []

  >>> ob.get({'b': (1, 3)})
  [ClassA(a=ClassB(c=1, d=2), b=1), ClassA(a=ClassB(c=4, d=3), b=3)]

  >>> ob = ObjectBase({'a': lambda x: x.d - x.c})
  >>> ob.get()
  []

  >>> ob = ObjectBase()
  >>> ob.put((x * x for x in range(4)))
  >>> ob.get()
  [0, 1, 4, 9]
  """
  class MaskManager(object):
    def __init__(self, values):
      self.__values = np.array(values)
      self.__cachedMasks = {}

    def getMask(self, selector):
      """
      >>> mm = ObjectBase.MaskManager([])
      >>> list(mm.getMask(lambda x: x != 0))
      []

      >>> list(mm.getMask(lambda x: x == 0))
      []

      >>> mm = ObjectBase.MaskManager([1, 2])
      >>> list(mm.getMask(lambda x: x != 0))
      [True, True]

      >>> list(mm.getMask(lambda x: x == 0))
      [False, False]

      >>> list(mm.getMask(lambda x: x > 1))
      [False, True]

      >>> list(mm.getMask([]))
      [False, False]

      >>> list(mm.getMask([1]))
      [True, False]

      >>> list(mm.getMask([1, 2]))
      [True, True]

      >>> list(mm.getMask([3,]))
      [False, False]

      >>> mm = ObjectBase.MaskManager([u'a', u'a', u'b'])
      >>> list(mm.getMask(['b']))
      [False, False, True]
      """
      if hasattr(selector, '__call__'):
        return selector(self.__values)

      return self.__combineMasks(selector)

    def __combineMasks(self, acceptedValues):
      if not acceptedValues:
        return np.zeros_like(self.__values, dtype=bool)

      # XXX: Python3 fix
      return self.__sumMasks(list(map(self.__getMasksMatchingValue, acceptedValues)))

    def __sumMasks(self, masks):
      if len(masks) == 1:
        return masks[0]

      return sum(masks[1:], masks[0])

    def __getMasksMatchingValue(self, value):
      try:
        return self.__cachedMasks[value]

      except KeyError:
        return self.__makeAndCacheMask(value)

    def __makeAndCacheMask(self, value):
      mask = self.__values == value
      self.__cachedMasks[value] = mask
      return mask


  def __init__(self, converters={}):
    """
    """
    self.__objects = np.array([], dtype=object)
    self.__cachedMaskManagers = {}
    self.__converters = dict(converters)

  def __len__(self):
    return len(self.__objects)

  def put(self, objects):
    self.__objects = np.append(self.__objects,
                               objects if isinstance(objects, Sequence) else list(objects))
    self.__cachedMaskManagers.clear()

  def get(self, filters=None):
    return list(self.__getFilteredObjects(filters))

  def __getFilteredObjects(self, filters):
    if filters:
      return self.__objects[self.__getProductOfMasks(filters)]

    return self.__objects
      
  def __getProductOfMasks(self, selectors):
    mask = True
    for attributeName, selector in selectors.items():
      mask = mask * self.__getMask(attributeName, selector)

    return mask

  def __getMask(self, attributeName, selector):
    return self.__getMaskManager(attributeName).getMask(selector)

  def __getMaskManager(self, attributeName):
    try:
      return self.__cachedMaskManagers[attributeName]

    except KeyError:
      maskManager = self.MaskManager(self.__getConvertedAttributeValues(attributeName))
      self.__cachedMaskManagers[attributeName] = maskManager
      return maskManager

  def __getConvertedAttributeValues(self, attributeName):
    attributeValues = self.getAttributes(attributeName)
    if attributeName in self.__converters:
      # XXX: Python3 fix - makes NumPy array working
      return list(map(self.__converters[attributeName], attributeValues))

    return attributeValues

  def getAttributes(self, *attributeNames):
    """
    >>> ob = ObjectBase()
    >>> ob.put([ClassA(ClassB(1, 2), 1), ClassA(ClassB(2, 3), 2),
    ...        ClassA(ClassB(4, 3), 3)])
    >>> ob.getAttributes('a')
    [ClassB(c=1, d=2), ClassB(c=2, d=3), ClassB(c=4, d=3)]

    >>> ob.getAttributes('b')
    [1, 2, 3]

    >>> ob.getAttributes('a.c')
    [1, 2, 4]

    >>> ob.getAttributes('a.c', 'b')
    [(1, 1), (2, 2), (4, 3)]

    >>> ob = ObjectBase()
    >>> ob.getAttributes('a.c')
    []

    >>> ob = ObjectBase({'a': lambda x: x.c})
    >>> ob.put([ClassA(ClassB(1, 2), 1)])
    >>> ob.getAttributes('a')
    [ClassB(c=1, d=2)]
    """
    # XXX: Python3 fix
    return list(map(attrgetter(*attributeNames), self.__objects))


if __name__ == '__main__':
  import doctest
  class ClassA(object):
    def __init__(self, a, b):
      self.a = a
      self.b = b

    def __repr__(self):
      return "ClassA(a=%s, b=%s)" % (repr(self.a), repr(self.b))

  class ClassB(object):
    def __init__(self, c, d):
      self.c = c
      self.d = d

    def __repr__(self):
      return "ClassB(c=%s, d=%s)" % (repr(self.c), repr(self.d))

  doctest.testmod(extraglobs={'ClassA': ClassA,
                              'ClassB': ClassB})
