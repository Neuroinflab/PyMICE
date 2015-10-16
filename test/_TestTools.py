#!/usr/bin/env python
# encoding: utf-8
###############################################################################
#                                                                             #
#    PyMICE library                                                           #
#                                                                             #
#    Copyright (C) 2015 Jakub M. Kowalski, S. Łęski (Laboratory of            #
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
from unittest import TestCase

if sys.version_info >= (3, 0):
   basestring = str

def allInstances(instances, cls):
  return all(isinstance(x, cls) for x in instances)


class Mock(object):
  def __init__(self, callers={}, **kwargs):
    self.sequence = []
    self.__callers = dict(callers)
    for k, v in kwargs.items():
      setattr(self, k, v)

  def __getattr__(self, item):
    def method(*args):
      self._registerCall(((item,) + args) if args else item)
      if item in self.__callers:
        try:
          return self.__callers[item][args]

        except TypeError:
          print('%s\t%s' % (item, args))
          raise

    return method

  def _registerCall(self, call):
    self.sequence.append(call)


class MockDictManager(Mock):
  def getManager(self, item):
    self._registerCall(('getManager', item))

  def __getitem__(self, item):
    self._registerCall(('__getitem__', item))
    return self.Cls(item) if item is not None else None


class MockIntDictManager(int, MockDictManager):
  def __init__(self, val=0, *args, **kwargs):
    MockDictManager.__init__(self, *args, **kwargs)
    self.items = {}

    class Cls(MockIntDictManager):
      pass

    self.Cls = Cls

  def __getitem__(self, item):
    self._registerCall(('__getitem__', item))
    try:
      return self.items[int(item)]

    except KeyError:
      output = self.Cls(item)
      self.items[output] = output
      return output


class MockStrDictManager(MockDictManager):
  def __init__(self, *args, **kwargs):
    super(MockStrDictManager, self).__init__(*args, **kwargs)

    class Cls(str):
      pass

    self.Cls = Cls


class MockCloneable(Mock):
  def clone(self, *args):
    self._registerCall((('clone',) + args) if args else 'clone')
    return Mock(_cloneOf=self)


class BaseTest(TestCase):
  longMessage = True
  def checkAttribute(self, obj, name, value=None, cls=None):
    # try:
      attr = getattr(obj, name)
      if value is None:
        self.assertIs(attr, None,
                      'Attribute: %s' % name)

      else:
        self.assertEqual(attr, value,
                         'Attribute: %s' % name)
        if cls is not None:
          self.assertIsInstance(attr, cls,
                                'Attribute: %s' % name)

    # except AssertionError:
    #   print(name)
    #   raise

  def checkAttributes(self, obj, testList):
    for test in testList:
      if isinstance(test, basestring):
        self.checkAttribute(obj, test)

      else:
        self.checkAttribute(obj, *test)

  def checkAttributeSeq(self, seq, name, tests):
    for obj, test in zip(seq, tests):
      if test is None:
        self.checkAttribute(obj, name)

      elif isinstance(test, tuple):
        self.checkAttribute(obj, name, *test)

      else:
        self.checkAttribute(obj, name, test)

  def checkObjectsEquals(self, a, b, skip=()):
    for attr in self.attributes:
      if attr in skip:
        continue

      # try:
      self.assertEqual(getattr(a, attr), getattr(b, attr),
                       'Attribute: %s' % attr)

      # except AssertionError:
      #   print(attr)
      #   raise
