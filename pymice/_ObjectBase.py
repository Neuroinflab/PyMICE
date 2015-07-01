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

class ObjectBase(object):
  """
  A base class for efficient object filtering.

  >>> ob = ObjectBase()
  >>> ob.get()
  []

  >>> ob.put([ClassA(1, 4)])
  >>> ob.get()
  [ClassA(a=1, b=4)]

  >>> ob.put([ClassA(2, 2)])
  >>> ob.get()
  [ClassA(a=1, b=4), ClassA(a=2, b=2)]

  >>> ob.put([ClassA(2, 2), ClassB(0, 0)])
  >>> ob.get()
  [ClassA(a=1, b=4), ClassA(a=2, b=2), ClassA(a=2, b=2), ClassB(c=0, d=0)]

  >>> tmp = ob.get()
  >>> tmp.append(1)
  >>> ob.get()
  [ClassA(a=1, b=4), ClassA(a=2, b=2), ClassA(a=2, b=2), ClassB(c=0, d=0)]

  >>> ob = ObjectBase([ClassA(1, 4), ClassA(2, 2), ClassA(2, 2)])
  >>> ob.get()
  [ClassA(a=1, b=4), ClassA(a=2, b=2), ClassA(a=2, b=2)]

  >>> tmp = ob.get()
  >>> tmp[2].b = 42
  >>> ob.get()
  [ClassA(a=1, b=4), ClassA(a=2, b=2), ClassA(a=2, b=42)]

  >>> tmp = []
  >>> ob = ObjectBase(tmp)
  >>> ob.put([ClassA(2, 2), ClassB(0, 0)])
  >>> tmp
  []

  >>> ob = ObjectBase([ClassA(1, 4)])
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

  >>> ob = ObjectBase([ClassA(ClassB(1, 2), 1), ClassA(ClassB(2, 3), 2),
  ...                  ClassA(ClassB(4, 3), 3)])
  >>> ob.get({'b': lambda x: (x == 1) + (x == 3)})
  [ClassA(a=ClassB(c=1, d=2), b=1), ClassA(a=ClassB(c=4, d=3), b=3)]

  >>> ob.get({'a.d': lambda x: x == 3})
  [ClassA(a=ClassB(c=2, d=3), b=2), ClassA(a=ClassB(c=4, d=3), b=3)]

  >>> ob = ObjectBase([ClassA(ClassB(1, 2), 1), ClassA(ClassB(2, 3), 2),
  ...                  ClassA(ClassB(4, 3), 3)],
  ...                 converters={'a': lambda x: x.d - x.c})
  >>> ob.get({'a': lambda x: x == 1})
  [ClassA(a=ClassB(c=1, d=2), b=1), ClassA(a=ClassB(c=2, d=3), b=2)]
  """
  def __init__(self, objects=[], converters={}):
    """
    """
    self.__objects = np.array(objects, dtype=object)
    self.__cachedAttributes = {}
    self.__converters = dict(converters)

  def put(self, objects):
    self.__objects = np.append(self.__objects, objects)
    self.__cachedAttributes.clear()

  def get(self, filters=None):
    return list(self.__getFilteredObjects(filters))

  def __getFilteredObjects(self, filters):
    if filters:
      return self.__objects[self.__getMask(filters)]

    else:
      return self.__objects
      
  def __getMask(self, filters):
    mask = True
    for attributeName, filterFunction in filters.items():
      mask = mask * filterFunction(self.__getAttributeValues(attributeName))

    return mask

  def __getAttributeValues(self, attributeName):
    try:
      return self.__cachedAttributes[attributeName]

    except KeyError:
      return self. __getAndCacheAttributeValues(attributeName)
      
  def __getAndCacheAttributeValues(self, attributeName):
    attributeValues = np.array(self.__getConvertedAttributeValues(attributeName))
    self.__cachedAttributes[attributeName] = attributeValues
    return attributeValues

  def __getConvertedAttributeValues(self, attributeName):
    attributeValues = map(attrgetter(attributeName), self.__objects)
    if attributeName in self.__converters:
      return map(self.__converters[attributeName], attributeValues)

    return attributeValues


if __name__ == '__main__':
  import doctest
  import collections
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
