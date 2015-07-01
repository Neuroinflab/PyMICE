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


class ObjectBase(object):
  """
  A base class for efficient onbject filtering.

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

  >>> ob = ObjectBase([1, 2, [1]])
  >>> ob.get()
  [1, 2, [1]]

  >>> tmp = ob.get()
  >>> tmp[2][0] = 42
  >>> ob.get()
  [1, 2, [42]]

  >>> tmp = []
  >>> ob = ObjectBase(tmp)
  >>> ob.put([1, 2])
  >>> tmp
  []
  """
  def __init__(self, objects=[]):
    """
    """
    self.__objects = list(objects)

  def put(self, objects):
    self.__objects.extend(objects)

  def get(self):
    return list(self.__objects)

if __name__ == '__main__':
  import doctest
  import collections
  ClassA = collections.namedtuple('ClassA', ['a', 'b'])
  ClassB = collections.namedtuple('ClassB', ['c', 'd'])

  doctest.testmod(extraglobs={'ClassA': ClassA,
                              'ClassB': ClassB})
