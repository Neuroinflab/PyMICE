#!/usr/bin/env python
# encoding: utf-8
###############################################################################
#                                                                             #
#    PyMICE library                                                           #
#                                                                             #
#    Copyright (C) 2015 Jakub M. Kowalski, (Laboratory of Neuroinformatics;   #
#    Nencki Institute of Experimental Biology)                                #
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

import unittest
from sys import getrefcount

from pymice._C import emptyStringToNone

class TestEmptyStringToNone(unittest.TestCase):
  def testEmptyList(self):
    self._checkList([], [])

  def testListOneStr(self):
    noneBefore = getrefcount(None)
    self._checkList(['a'], ['a'])
    noneAfter = getrefcount(None)
    self.assertEqual(noneBefore, noneAfter)

  def testListOneEmpty(self):
    empty = ''
    self._checkReplace([empty], [None], 1, empty)

  def testListTwoEmpty(self):
    empty = ''
    self._checkReplace([empty, 'something', empty],
                       [None, 'something', None],
                        2, empty)

  def testNotList(self):
    self.assertRaises(TypeError, lambda: emptyStringToNone(()))

  def testNotBasestring(self):
    empty = ''
    self._checkReplace([empty, 'something', ()],
                       [None, 'something', ()],
                       1, empty)

  def testUnicode(self):
    empty = u''
    self._checkReplace([empty, u'something', empty],
                       [None, u'something', None],
                        2, empty)

  def testNestedList(self):
    empty = ''
    self._checkReplace([empty, u'something', [empty]],
                       [None, u'something', [None]],
                        2, empty)

  def _checkReplace(self, before, after, changed, empty):
    noneBefore = getrefcount(None)
    emptyBefore = getrefcount(empty)
    self._checkList(before, after)
    noneAfter = getrefcount(None)
    emptyAfter = getrefcount(empty)
    self.assertEqual(noneBefore + changed, noneAfter)
    self.assertEqual(emptyBefore - changed, emptyAfter)

  def _checkList(self, listIn, after):
    refsBefore = getrefcount(listIn)
    listOut = emptyStringToNone(listIn)
    refsAfter = getrefcount(listIn)
    self.assertIs(listIn, listOut)
    self.assertEqual(refsBefore + 1, refsAfter)
    self.assertEqual(listOut, after)
    return listOut

if __name__ == '__main__':
  unittest.main()