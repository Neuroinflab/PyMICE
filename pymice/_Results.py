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

import os 
import csv
import warnings

class ResultsCSV(object):
  def __init__(self, filename, fields=(), force=False):
    self.__fields = set(fields)
    self.__rows = {}
    self.__currentID = None
    self.__nextID = 0
    if os.path.exists(filename) and not force:
      raise ValueError("File %s already exists." % filename)

    self.__fh = open(filename, 'wb')

  def __enter__(self):
    return self

  def __exit__(self, type, value, traceback):
    self.close()

  def __del__(self):
    self.close()

  def close(self):
    if self.__fh is None:
      return

    fields = sorted(self.__fields)
    writer = csv.writer(self.__fh)

    writer.writerow([f.encode('utf-8') for f in fields])
    for row in self.__rows.values():
      line = [unicode(row.get(f, '')).encode('utf-8') for f in fields]
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

    self.__fields.add(field)

    try:
      row = self.__rows[id]

    except KeyError:
      warnings.warn('Row of ID %s not found, creating a new row.' % id)
      row = self.__rows[self.addRow(id)]

    if field in row:
      warnings.warn('Field %s already set for row of ID %s, overwriting.' % (field, id))
      
    row[field] = value
