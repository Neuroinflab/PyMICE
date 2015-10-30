#!/usr/bin/env python
# encoding: utf-8
###############################################################################
#                                                                             #
#    PyMICE library                                                           #
#                                                                             #
#    Copyright (C) 2014-2015 Jakub M. Kowalski (Laboratory of                 #
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
import os
import time

from datetime import datetime

import zipfile
import csv
import warnings

import operator

import cStringIO

convertFloat = operator.methodcaller('replace', ',', '.')

class ICFixer(object):
  _fnAliases = {'IntelliCage/Groups.txt': 'Groups.txt'}
  _aliasesZip = {'Animals.txt': {'AnimalName': 'Name',
                             'AnimalTag': 'Tag',
                             'GroupName': 'Group',
                             'AnimalNotes': 'Notes',
                            },
                 'Groups.txt': {'GroupName': 'Name',
                            'GroupNotes': 'Notes',
                            'ModuleName': 'Module',
                           },
                 'IntelliCage/Visits.txt': {'AnimalTag': 'Tag',
                                        'Animal': 'Tag', 
                                        'ID': 'VisitID',
                                        'ModuleName': 'Module',
                                       },
                 'IntelliCage/Nosepokes.txt': {'LicksNumber': 'LickNumber',
                                           'LicksDuration': 'LickDuration',
                                          },
                 'IntelliCage/Log.txt': {'LogType': 'Type',
                                     'Log': 'Type',
                                     'LogCategory': 'Category',
                                     'LogNotes': 'Notes',
                                    },
                 'IntelliCage/HardwareEvents.txt': {'HardwareType': 'Type',
                                               },
                }
  _convertZip = {'IntelliCage/Visits.txt': {#'Tag': int,
                                        #'Start': convertTimeAux,
                                        #'End': convertTimeAux,
                                        #'ModuleName': convertStr,
                                        #'Cage': int,
                                        #'Corner': int,
                                        'CornerCondition': convertFloat,
                                        'PlaceError': convertFloat,
                                        #'AntennaNumber': convertInt,
                                        'AntennaDuration': convertFloat,
                                        #'PresenceNumber': convertInt,
                                        'PresenceDuration': convertFloat,
                                        #'VisitSolution': convertInt,
                                       },
                 'IntelliCage/Nosepokes.txt': {
                                           #'Start': convertTimeAux,
                                           #'End': convertTimeAux,
                                           #'Side': int,
                                           #'LickNumber': int,
                                           'LickContactTime': convertFloat,
                                           'LickDuration': convertFloat,
                                           'SideCondition': convertFloat,
                                           'SideError': convertFloat,
                                           'TimeError': convertFloat,
                                           'ConditionError': convertFloat,
                                           #'AirState': convertInt,
                                           #'DoorState': convertInt,
                                           #'LED1State': convertInt,
                                           #'LED2State': convertInt,
                                           #'LED3State': convertInt,
                                          },
                 'IntelliCage/Log.txt': {#'DateTime': convertTimeAux,
                                     #'Category': convertStr,
                                     #'Type': convertStr,
                                     #'Cage': convertInt,
                                     #'Corner': convertInt,
                                     #'Side': convertInt,
                                     #'Notes': convertStr,
                                    },
                 'IntelliCage/Environment.txt': {#'DateTime': convertTimeAux,
                                             'Temperature': convertFloat,
                                             #'Illumination': convertInt,
                                             #'Cage': convertInt,
                                            },
                 'IntelliCage/HardwareEvents.txt': {#'DateTime': convertTimeAux,
                                                #'Type': convertInt,
                                                #'Cage': convertInt,
                                                #'Corner': convertInt,
                                                #'Side': convertInt,
                                                #'State': convertInt,
                                               },
                }

  def _fixData(self, data, convertors=None):
    if convertors:
      data = dict((k, map(convertors[k], v) if k in convertors else v) for (k, v) in data.items())

    return data

  def toZIP(self, fnameOut, tzOut=None):
    if tzOut and self.tz:
      def convertTime(tStr):
        tSplit = tStr.replace('-', ' ').replace(':', ' ').split()
        subSec = float(tSplit[5]) if len(tSplit) == 6 else 0.
        sec = int(subSec)
        ms = (1000000 * (subSec - sec))
        dt = datetime(*(map(int, tSplit[:5]) + [sec, ms]))
        dt = self.tz.localize(dt, None) # FIXME: mwahahaha!!!
        dt = dt.astimezone(tzOut)
        return dt.strftime('%Y-%m-%d %H:%M:%S.%f')

    else:
      convertTime = None

    zfIn = zipfile.ZipFile(self.fname)
    zfOut = zipfile.ZipFile(fnameOut, 'w')

    for src in zfIn.namelist():
      dst = self._fnAliases.get(src, src)
      if dst in self._aliasesZip or dst in self._convertZip:
        labels, data = self.fromCSV(zfIn.open(src))
        aliases = self._aliasesZip.get(dst)

        if aliases:
          labels = [aliases.get(l, l) for l in labels]
          data = dict((aliases.get(l, l), d) for (l, d) in data.items())

        data = self._fixData(data, self._convertZip.get(dst))

        buf = cStringIO.StringIO()
        self.toCSV(buf, data, labels=labels)
        zfOut.writestr(dst, buf.getvalue(),
                       zipfile.ZIP_DEFLATED)

      else:
        buf = zfIn.read(src)
        zfOut.writestr(dst, buf, zipfile.ZIP_DEFLATED)

    zfOut.close()

  def __init__(self, fname, tz=None):
    """
    """
    self.fname = fname
    self.tz = tz

  @staticmethod
  def fromCSV(fname):
    """
    Read data from the CSV file into directory of lists.

    @type fname: str or file object
    """
    result = None

    if type(fname) is str:
      fname = open(fname)

    reader = csv.reader(fname, delimiter='\t')
    try:
      labels = reader.next()
      data = [x for x in reader]
      n = len(data)
      if n > 0:
        data = zip(*data)

      else:
        data = [[] for x in labels]

      result = dict(zip(labels, data))

    except StopIteration:
      pass

    finally:
      fname.close()

    return labels, result

  @staticmethod
  def toCSV(fname, data, labels=None):
    """
    Store data (a directory of equaly long lists) to the CSV file.

    @type fname: file object
    @type data: dict
    """
    if len(data) == 0:
      return

    if labels is None:
      labels = data.keys()

    data = [data[l] for l in labels]

    writer = csv.writer(fname, delimiter='\t')
    writer.writerow(labels)
    writer.writerows(zip(*data))


if __name__ == '__main__':
  if len(sys.argv) != 3:
    print 'Usege: %s <src> <dst>' % sys.argv[0]

  else:
    icf = ICFixer(sys.argv[1])
    icf.toZIP(sys.argv[2])
