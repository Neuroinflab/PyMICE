#!/usr/bin/env python
# encoding: utf-8
###############################################################################
#                                                                             #
#    PyMICE library                                                           #
#                                                                             #
#    Copyright (C) Jakub M. Kowalski (Laboratory of Neuroinformatics;         #
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

import sys
import os 
import csv

from ._Tools import warn

class ResultsCSV(object):
  def __init__(self, filename, fields=(), force=False):
    self.__fields = set(fields)
    self.__fieldsOrder = list(fields)
    self.__rows = {}
    self.__rowOrder = []
    self.__currentID = None
    self.__nextID = 0
    if os.path.exists(filename) and not force:
      raise ValueError("File %s already exists." % filename)

    if sys.version_info < (3, 0):
      self.__fh = open(filename, 'wb')

    else:
      self.__fh = open(filename, 'w', newline='')

  def __enter__(self):
    return self

  def __exit__(self, type, value, traceback):
    self.close()

  def __del__(self):
    self.close()

  def close(self, inOrder=False):
    if self.__fh is None:
      return

    fields = self.__fieldsOrder if inOrder else sorted(self.__fields)
    writer = csv.writer(self.__fh)

    if sys.version_info < (3, 0):
      writer.writerow([f.encode('utf-8') for f in fields])

    else:
      writer.writerow(fields)

    for row in [self.__rows[id] for id in self.__rowOrder]:
      if sys.version_info < (3, 0):
        line = [unicode(row.get(f, '')).encode('utf-8') for f in fields]

      else:
        line = [str(row.get(f, '')) for f in fields]

      writer.writerow(line)

    self.__fh.close()
    self.__fh = None

  def addRow(self, id=None):
    if id is None:
      while True:
        id = self.__nextID
        self.__nextID += 1
        if id not in self.__rows:
          break

    elif id in self.__rows:
      raise ValueError('Row of ID %s already exists.' % id)

    self.__current = {}
    self.__rows[id] = self.__current
    self.__rowOrder.append(id)
    self.__currentID = id
    return id

  def setRow(self, id):
    self.__current = self.__rows[id]
    self.__currentID = id
    return id

  def getRow(self):
    return self.__currentID
      
  def addField(self, field, value='', id=None):
    if id is None:
      id = self.__currentID
      if id is None:
        raise ValueError('Row ID must be given if no row has been chosen yet.')

    self._declareField(field)

    try:
      row = self.__rows[id]

    except KeyError:
      warn.warn('Row of ID %s not found, creating a new row.' % id)
      row = self.__rows[self.addRow(id)]

    if field in row:
      warn.warn('Field %s already set for row of ID %s, overwriting.' % (field, id))
      
    row[field] = value
    
  def declareFields(self, *fields):
    for field in fields:
        self._declareField(field)
        
  def _declareField(self, field):
    if field not in self.__fields:
      self.__fields.add(field)
      self.__fieldsOrder.append(field)

  def getField(self, field, id=None):
    if id is None:
      id = self.__currentID
      if id is None:
        raise ValueError('Row ID must be given if no row has been chosen yet.')

    if field not in self.__fields:
      raise KeyError('Unknown field: %s.' % field)

    try:
      row = self.__rows[id]

    except KeyError:
      raise KeyError('Unknown ID: %s.' % id)

    try:
      return row[field]

    except KeyError:
      raise KeyError('Field %s not set for ID %s.' % (field, id))
