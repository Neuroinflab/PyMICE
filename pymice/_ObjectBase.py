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

  >>> ob.push([ClassA(1, 4)])
  >>> ob.get()
  [ClassA(1, 4)]
  """
  def __init__(self):
    """
    """
    pass

  def put(self, objects):
    pass

  def get(self):
    return []

if __name__ == '__main__':
  import doctest
  import collections
  ClassA = collections.namedtuple('ClassA', ['a', 'b'])
  ClassB = collections.namedtuple('ClassB', ['c', 'd'])

  doctest.testmod(extraglobs={'ClassA': ClassA,
                              'ClassB': ClassB})
