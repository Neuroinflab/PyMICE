#!/usr/bin/env python
# encoding: utf-8
"""
_Data.py

Copyright (c) 2012-2014 Laboratory of Neuroinformatics. All rights reserved.
"""

import sys
import os
import datetime
import pytz
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.path import Path
from matplotlib import rc
import time
import zipfile
import csv
import cStringIO
import sqlite3
import codecs
import copy
import warnings
from math import exp, modf
import itertools
from operator import itemgetter, methodcaller, attrgetter
from ICNodes import DataNode, AnimalNode, GroupNode, VisitNode, NosepokeNode,\
                    LogNode, EnvironmentNode, HardwareEventNode

callCopy = methodcaller('copy')

def timeString(x, tz=None):
  return datetime.datetime.fromtimestamp(x, tz).strftime('%Y-%m-%d %H:%M:%S.%f%z')

def deprecated(message, warningClass=DeprecationWarning, stacklevel=1):
  warnings.warn(message, warningClass, stacklevel=2+stacklevel)

def ensureFloat(x):
  if isinstance(x, (str, unicode)):
    if x == '':
      return None

    return float(x.replace(',', '.'))

  if x != None:
    return float(x)

def ensureInt(x):
  if x == '' or x == None:
    return None

  if x != None:
    return int(x)

def hTime(t):
  dec, integer = modf(t)
  return time.strftime("%Y-%m-%d %H:%M:%S" + ('%01.3f' % dec)[1:],
                       time.localtime(integer))


def quoteIdentifier(s, errors="strict"):
  if isinstance(s, tuple):
    return '.'.join(quoteIdentifier(x, errors=errors) for x in s)

  encodable = s.encode("utf-8", errors).decode("utf-8")

  nul_index = encodable.find("\x00")
  if nul_index >= 0:
    error = UnicodeEncodeError("NUL-terminated utf-8", encodable,
                               nul_index, nul_index + 1, "NUL not allowed")
    error_handler = codecs.lookup_error(errors)
    replacement, _ = error_handler(error)
    encodable = encodable.replace("\x00", replacement)

  return '"%s"' % encodable.replace('"', '""')



class IMiceTemporal(object):
  def getStartTimes(self, mice=None):
    raise NotImplementedError("Virtual method called")

  def getstarttimes(self, *arg, **kwarg):
    print "WARNING: Deprecated method getstarttimes() called."
    return self.getStartTimes(*arg, **kwarg)

  def getEndTimes(self, mice=None):
    raise NotImplementedError("Virtual method called")

  def getendtimes(self, *arg, **kwarg):
    print "WARNING: Deprecated method getendtimes() called."
    return self.getEndTimes(*arg, **kwarg)

  def getDurations(self, mice=None):
    raise NotImplementedError("Virtual method called")

  def getdurations(self, *arg, **kwarg):
    print "WARNING: Deprecated method getdurations() called."
    return self.getDurations(*arg, **kwarg)

  def getProperty(self, fieldName, mice=None):
    raise NotImplementedError("Virtual method called")

  def getproperty(self, mice, propname, astype=None):
    print "WARNING: Deprecated method getproperty() called."
    print "         Does not work for fields of tables other than visits."
    if astype is None:
      return self.getProperty(propname, mice)

    if astype == 'float':
      return map(float, self.getProperty(propname, mice))


class IMiceSpatiotemporal(IMiceTemporal):
  def getLocations(self, mice=None):
    raise NotImplementedError("Virtual method called")


class IMiceLoader(IMiceSpatiotemporal):
  def getCorners(self, *arg, **kwarg):
    print "WARNING: Deprecated method getCorners() called."
    return self.getLocations(*arg, **kwarg)

  def getcorners(self, *arg, **kwarg):
    print "WARNING: Deprecated method getcorners() called."
    return self.getCorners(*arg, **kwarg)

  def getCornerConditions(self, mice=None):
    raise NotImplementedError("Virtual method called")

  def getcornerconditions(self, *arg, **kwarg):
    print "WARNING: Deprecated method getcornerconditions() called."
    return self.getCornerConditions(*arg, **kwarg)

  def getCage(self, mice):
    raise NotImplementedError("Virtual method called")

  def getTag(self, mice):
    raise NotImplementedError("Virtual method called")

  def getMiceFitterData(self, mice=None):
    raise NotImplementedError("Virtual method called")

  def getSocialBoxData(self):
    raise NotImplementedError("Virtual method called")

  def getAnimalGateData(self):
    raise NotImplementedError("Virtual method called")

  def getExcludedData(self):
    print "WARNING: Deprecated method getExcludedData() called."
    return self.excluded

  def getMice(self):
    raise NotImplementedError("Virtual method called")

  def getGroup(self, group = None):
    raise NotImplementedError("Virtual method called")

  def newGroup(self, group, mice = set()):
    raise NotImplementedError("Virtual method called")

  def __getMice(self):
    print "WARNING: Deprecated attribute mice accessed."
    return self.getMice()

  mice = property(__getMice)

  def __getGroup(self):
    print "WARNING: Deprecated attribute groups accessed."
    return dict((g, self.getGroup(g)) for g in self.getGroup())

  groups = property(__getGroup)

  def getInmates(self, cage = None):
    raise NotImplementedError("Virtual method called")

  def __getInmates(self):
    print "WARNING: Deprecated attribute cages accessed."
    return dict((c, self.getInmates(c)) for c in self.getInmates())

  cages = property(__getInmates)


class SQLiteDatabased(object):
  class TableDict(dict):
    def __init__(self, *args, **kwargs):
      dict.__init__(self, *args, **kwargs)
      vs = self.values()
      if len(vs) == 0:
        self.__rowcount = None
        return

      rc = len(vs[0])
      if any(len(v) != rc for v in vs):
        raise ValueError('List given as values differ in length.')

      self.__rowcount = rc

    def __setitem__(self, k, v):
      if self.__rowcount not in (None, len(v)):
        raise ValueError('An attempt to insert a list of different length than rowcount.')

      dict.__setitem__(self, k, v)
      if self.__rowcount is None:
        self.__rowcount = len(v)

    @classmethod
    def wrapRows(cls, keys, rows):
      values = zip(*rows)
      if len(keys) != len(values):
        raise ValueError('Keys to columns mismatch')

      return cls(zip(keys, values))

    def select(self, *keys):
      #assert all(k in self for k in keys)

      if len(keys) == 0:
        keys = sorted(self.keys())

      return zip(*[self[k] if k in self else [None] * self.__rowcount for k in keys])

    def __getRowcount(self):
      return self.__rowcount

    rowcount = property(__getRowcount)

  def __init__(self, structure={}, database=':memory:', verbose=False, joins=[]):
    # Masking - by default do not mask
    self.unmaskData()
    self._verbose = verbose
    self.structure = structure

    self.db = sqlite3.connect(database)
    self.db.create_function('exp', 1, exp)

    self.__mask = {}
    self.__maskId = 0
    self.__joins = {}

    if len(joins) > 0:
      joinGraph = {}
      newTrees = {}
      newPaths = {}
      for (ta, tb), fields in joins:
        fieldStr = ', '.join(quoteIdentifier(f) for f in fields)
        for t1, t2 in [(ta, tb), (tb, ta)]:
          assert t1 in structure
          if t1 not in joinGraph:
            joinGraph[t1] = {}

          assert t2 not in joinGraph[t1]
          joinGraph[t1][t2] = fieldStr

        key = frozenset([ta, tb])
        newTrees[frozenset([ta, tb])] = '%s JOIN %s USING(%s)' % (t1, t2, fieldStr)
        newPaths[key] = key


      # test if one tree given
      assert len(joins) + 1 == len(joinGraph)
      toVisit = [joins[0][0][0]]
      visited = set()
      while len(toVisit) > 0:
        v = toVisit.pop(0)
        #print v, toVisit, visited
        if v not in visited:
          nv = joinGraph[v]
          toVisit.extend(nv)
          visited.add(v)

      assert len(visited) == len(joinGraph)

      trees = {}
      while len(newTrees) > 0:
        lastTrees = newTrees
        newTrees = {}
        trees.update(lastTrees)
        for tree, joinClause in lastTrees.items():
          for v in tree:
            for nv, fieldStr in joinGraph[v].items():
              if nv not in tree:
                key = tree | frozenset([nv])
                if key not in newTrees:
                  newTrees[key] = '%s JOIN %s USING(%s)' % (joinClause, nv, fieldStr)

      paths = {}
      while len(newPaths) > 0:
        lastPaths = newPaths
        newPaths = {}
        paths.update(lastPaths)
        for ends, pth in lastPaths.items():
          for v in ends:
            for nv in joinGraph[v]:
              if nv not in pth:
                key = ends ^ frozenset([v, nv])
                if key not in newPaths:
                  newPaths[key] = pth | frozenset([nv])

      for l in range(2, len(joinGraph) + 1):
        for tables in itertools.combinations(joinGraph, l):
          v = tables[0]
          tree = frozenset.union(*[paths[frozenset([v, t])] for t in tables[1:]])
          self.__joins[frozenset(tables)] = trees[tree]


    # TODO: some reverse ingeneering
    for name, fields in structure.items():
      fieldString = ', '.join('%s %s' % (k.lower(), v)\
                              for (k, v) in fields.items())
      query = "CREATE TABLE %s (%s);" % (name.lower(), fieldString)
      if verbose:
        print query

      self.db.execute(query)

      self.__mask[name] = {}

    self.db.commit()

  def selectAllDataSmart(self, tables, fields=None, aliases={}):
    if isinstance(tables, basestring):
      tables = (tables,)

    if isinstance(fields, basestring):
      fields = (fields,)

    elif fields is None:
      if len(tables) == 1:
        fields = list(self.structure[tables[0]])

      else:
        fields = [(table, f) for f in self.structure[table] for table in tables]

    safeFields = map(quoteIdentifier, fields)
    data = zip(*self.getMaskedSQLSmart(safeFields, tables))

    if len(data) == 0:
      return None

    labels = [aliases.get(f, f) for f in fields]
    return self.TableDict(zip(labels, data))

  def getMaskedSQLSmart(self, safeFields, tables, where=(), whereData=(), order=None):
    unwrap = isinstance(safeFields, basestring)
    if unwrap:
      safeFields = (safeFields,)

    selectClause = ', '.join(safeFields)
    fromClause = self._getFromClause(tables)
    orderClause = '' if order is None else "ORDER BY %s" % order
    mask = self._getTableMask(tables) + where
    if len(mask) > 0:
      maskClause = ' AND '.join(mask)
      query = 'SELECT %s FROM %s WHERE %s %s;' % (selectClause, fromClause, maskClause, orderClause)

    else:
      query = 'SELECT %s FROM %s %s;' % (selectClause, fromClause, orderClause)

    #print query, whereData

    return self.getSQL(query, whereData, unwrap)


  def _getFromClause(self, tables):
    if isinstance(tables, basestring):
      return tables

    if len(tables) == 0:
      return tables[0]

    return self.__joins[frozenset(tables)]

  # more flexible table masking
  def _maskTable(self, table, condition, name = None):
    if name is None:
      name = "constraint %d" % self.__maskId
      self.__maskId += 1

    self.__mask[table][name] = condition
    return name

  def _unmaskTable(self, table, name = None):
    if name is None:
      self.__mask[table] = {}

    else:
      del self.__mask[table][name]

  def _getTableMask(self, tables):
    if isinstance(tables, basestring):
      tables = (tables,)

    return sum((tuple(self.__mask[table].values()) for table in tables), ())

  def insertData(self, data, table):
    """
    Insert data into table according to the present database structure.
    Extend the structure if necessary.
    """
    safeTable = quoteIdentifier(table)

    # prepare table
    if table in self.structure:
      newLabels = [label for label in data\
                   if label not in self.structure[table]]

      for label in newLabels:
        self.structure[table][label] = 'TEXT'
        safeLabel = quoteIdentifier(label)
        query = "ALTER TABLE %s ADD COLUMN %s TEXT;" % (safeTable, safeLabel)
        if self._verbose:
          print query

        self.db.execute(query)

    else:
      self.structure[table] = dict((l, 'TEXT') for l in data)

      labelString = ', '.join("%s TEXT" % quoteIdentifier(l) for l in data)
      query = "CREATE TABLE %s(%s);" % (safeTable, labelString)

      if self._verbose:
        print query

      self.db.execute(query)

    newdata = {}
    for label, values in data.items():
      if self.structure[table][label] == 'INTEGER':
        newdata[label] = map(ensureInt, values)

      elif self.structure[table][label] == 'REAL':
        newdata[label] = map(ensureFloat, values)

      else:
        newdata[label] = values

    labels, rows = zip(*(newdata.items()))
    rows = zip(*rows)

    tableString = "%s(%s)" % (safeTable, ', '.join(quoteIdentifier(l) for l in labels))
    query = "INSERT INTO %s VALUES (%s);" % (tableString, ', '.join('?' for l in labels))
    #if self._verbose:
    #    print query

    self.db.executemany(query, rows)
    self.db.commit()

  # TODO: data masking?
  def selectAllData(self, table):
    if table not in self.structure:
      raise KeyError("Table of name %s does not exist." % table)

    safeTable = quoteIdentifier(table)
    labels = self.structure[table].keys()
    safeLabels = [quoteIdentifier(l) for l in labels]

    mask =  self._getTableMask(table)

    if len(mask) == 0:
      query = "SELECT %s FROM %s;" % (', '.join(safeLabels), safeTable)

    else:
      query = "SELECT %s FROM %s WHERE %s;" % (', '.join(safeLabels), safeTable, ' AND '.join(mask))

    cursor = self.db.execute(query)
    data = zip(*cursor.fetchall())
    if len(data) == 0:
      return None

    return self.TableDict(zip(labels, data))

  def unmaskData(self):
    self.mask = []

  def _getMask(self):
    return tuple(self.mask);

  def getSQL(self, query, data = (), unwrap = True):
    #print query
    cursor = self.db.execute(query, data)

    if unwrap:
      return [x[0] for x in cursor]

    return cursor.fetchall()

  def getMaskedSQL(self, fromClause, fields=('*',), where = (), whereData = (),
                   order=None, timeStart=None, timeEnd=None):
    unwrap = isinstance(fields, basestring)

    if unwrap:
      fields = (fields,)

    selectClause = ', '.join(fields)

    whereClause = tuple(where) + self._getMask(timeStart=timeStart,
                                               timeEnd=timeEnd)
    whereClause = ' AND '.join('(%s)' % x for x in whereClause)
    if whereClause != '':
      whereClause = " WHERE %s" % whereClause

    orderClause = '' if order == None else "ORDER BY %s" % order

    query = """
            SELECT %s
            FROM %s
            %s
            %s;
            """ % (selectClause, fromClause, whereClause, orderClause)
    #print query
    #print whereData

    return self.getSQL(query, sum(whereData, ()), unwrap)


class ISQLiteDatabasedMiceData(IMiceLoader):
  def getFilteredSQL(self, fields=('*',), mice=None, fromClause='visits', where = (), whereData = (), order=''):
    raise NotImplementedError("Virtual method called")

  def getLocations(self, mice=None):
    """
    >>> ml_l1.getLocations()
    [4, 1, 2]
    >>> ml_icp3.getLocations()
    [1, 2, 3]
    >>> ml_l1.getLocations('Mickey')
    [1]
    >>> ml_icp3.getLocations('Jerry')
    [3]
    >>> ml_l1.getLocations(['Mickey', 'Minnie'])
    [4, 1]
    >>> ml_icp3.getLocations(['Jerry', 'Minnie'])
    [1, 3]
    """
    deprecated("Obsolete method getLocations() called.",
               PendingDeprecationWarning)
    return [v.Corner for v in self.getVisits(mice=mice, order='start, end')]

  def getCornerConditions(self, mice=None):
    deprecated("Obsolete method getCornerConditions() called.",
               PendingDeprecationWarning)
    return [v.CornerConditions for v in self.getVisits(mice=mice, order='start, end')]

  def getStartTimes(self, mice=None):
    """
    >>> for t in ml_icp3.getStartTimes():
    ...   print hTime(t)
    2012-12-18 12:13:14.139
    2012-12-18 12:18:55.421
    2012-12-18 12:19:55.421

    >>> for t in ml_l1.getStartTimes('Minnie'):
    ...   print hTime(t)
    2012-12-18 12:30:02.360
    """
    deprecated("Obsolete method getStartTimes() called.",
               PendingDeprecationWarning)
    return [v.Start for v in self.getVisits(mice=mice, order='start, end')]

  def getEndTimes(self, mice=None):
    deprecated("Obsolete method getEndTimes() called.",
               PendingDeprecationWarning)
    return [v.End for v in self.getVisits(mice=mice, order='start, end')]

  def getDurations(self, mice=None):
    deprecated("Obsolete method getDurations() called.",
               PendingDeprecationWarning)
    return [v.End - v.Start for v in self.getVisits(mice=mice, order='start, end')]

  def getProperty(self, fieldName, mice=None):
    deprecated("Obsolete method getProperty() called.",
               PendingDeprecationWarning)
    return [getattr(v, fieldName) for v in self.getVisits(mice=mice, order='start, end')]


  def getData(self, tableName='Visits', debug=False):
    deprecated("Obsolete method getData() called.",
               PendingDeprecationWarning)
    raise NotImplementedError('Unknown or not implemented data requested')


class Data(SQLiteDatabased, ISQLiteDatabasedMiceData):
  autoJoins = [(('visits', 'nosepokes'), ('_vid',))]

  defaultStructure = {'visits': {
#                                 'VisitID': 'INTEGER',
#                                 'AnimalTag': 'INTEGER',
                                 'Start': 'REAL',
                                 'End': 'REAL',
                                 'Module': 'TEXT',
                                 'Cage': 'INTEGER',
                                 'Corner': 'INTEGER',
                                 'CornerCondition': 'REAL',
                                 'PlaceError': 'REAL',
                                 'AntennaNumber': 'INTEGER',
                                 'AntennaDuration': 'REAL',
                                 'PresenceNumber': 'INTEGER',
                                 'PresenceDuration': 'REAL',
                                 'VisitSolution': 'INTEGER',
                                 '_vid': 'INTEGER',
                                 '_aid': 'INTEGER',
                                 },
                      'environment': {'DateTime': 'REAL',
                                      'Temperature': 'REAL',
                                      'Illumination': 'INTEGER',
                                      'Cage': 'INTEGER',
                                      },
                      'HardwareEvents': {'DateTime': 'REAL',
                                         'HardwareType': 'INTEGER',
                                         'Cage': 'INTEGER',
                                         'Corner': 'INTEGER',
                                         'Side': 'INTEGER',
                                         'State': 'INTEGER',
                                         },
                      'log': {'DateTime': 'REAL',
                              'Category': 'TEXT',
                              'Type': 'TEXT',
                              'Cage': 'INTEGER',
                              'Corner': 'INTEGER',
                              'Side': 'INTEGER',
                              'Notes': 'TEXT',
                              },
                      'nosepokes': {
#                                    'VisitID': 'INTEGER',
                                    'Start': 'REAL',
                                    'End': 'REAL',
                                    'Side': 'INTEGER',
                                    'LickNumber': 'INTEGER',
                                    'LickContactTime': 'REAL',
                                    'LickDuration': 'REAL',
                                    'SideCondition': 'REAL',
                                    'SideError': 'REAL',
                                    'TimeError': 'REAL',
                                    'ConditionError': 'REAL',
                                    'AirState': 'INTEGER',
                                    'DoorState': 'INTEGER',
                                    'LED1State': 'INTEGER',
                                    'LED2State': 'INTEGER',
                                    'LED3State': 'INTEGER',
                                    '_vid': 'INTEGER',
                                    },
# NOT UPDATED YET
#                      'animalgatesessions': {'Id': 'INTEGER',
#                                             'Tag': 'INTEGER',
#                                             'Start': 'REAL',
#                                             'End': 'REAL',
#                                             'Address': 'INTEGER',
#                                             'Direction': 'TEXT',
#                                             'IdSectionVisited': 'INTEGER',
#                                             'StandbySectionVisited': 'INTEGER',
#                                             'Weight': 'REAL',
#                                             },
#                      'socialboxregistrations': {'Tag': 'INTEGER',
#                                                 'Start': 'REAL',
#                                                 'End': 'REAL',
#                                                 'CageAddress': 'INTEGER',
#                                                 'Address': 'INTEGER',
#                                                 'Outer': 'INTEGER',
#                                                 }
                                              }

  def __init__(self, verbose = False, getNpokes=False, getLogs=False,
               getEnv=False, getHw=False):
    structure = copy.deepcopy(self.defaultStructure)
    SQLiteDatabased.__init__(self, structure, verbose = verbose, joins = self.autoJoins)

    self.__name2group = {}

    self._getNpokes = getNpokes
    self._getLogs = getLogs
    self._getEnv = getEnv
    self._getHw = getHw

    # change to
    self.__animals = []
    self.__animalsByName = {}

    self.__visits = []
    self.__nosepokes = [] #reserved for future use
    self.__logs = []
    self.__environment = []
    self.__hardware = []

  @property
  def _get_npokes(self):
    deprecated("Obsolete attribute _get_npokes accessed.")
    return self._getNpokes

  def __del__(self):
    for vNode in self.__visits:
      if vNode:
        vNode._del_()


# caching data
  def _initCache(self):
    self.icSessionStart = None
    self.icSessionEnd = None
    self.__mice = {}
    self.__cages = {}
    self.__animal2cage = {}

  def _buildCache(self):
    # build cache
    self.__mice = dict((k, v._aid) for (k, v) in self.__animalsByName.items())
    self.__cages = {}
    self.__animal2cage = {}
    currentCage = None
    animals = []
    #cursor = sorted(set((int(v.Cage), unicode(v.Animal.Name)) for v in self.__visits))
    cursor = self.db.execute('SELECT DISTINCT cage, _aid FROM visits ORDER BY cage')

    for cage, animal in cursor:
      animal = self.__animals[animal].Name
      if animal not in self.__animal2cage:
        self.__animal2cage[animal] = [cage]

      else:
        self.__animal2cage[animal].append(cage)
        print "WARNING: Animal %s found in multiple cages (%s)." %\
              (animal, ', '.join(map(str, self.__animal2cage[animal])))

      if cage != currentCage:
        if currentCage != None:
          self.__cages[currentCage] = frozenset(animals)

        animals = [animal]
        currentCage = cage

      else:
        animals.append(animal)

    #XXX: I've changed the indent (was in for loop) - in case of any issue
    #     investigate it.
    if currentCage != None:
      self.__cages[currentCage] = frozenset(animals)

    for animal in self.getMice():
      if animal not in self.__animal2cage:
        self.__animal2cage[animal] = []

  def getCage(self, mouse):
    cages = self.__animal2cage[mouse]
    if len(cages) != 1:
      if len(cages) == 0:
        print "WARNING: Mouse not found in any cage."
        return None

      print "WARNING: Animal %s found in multiple cages: %s."\
            % (mouse, ', '.join(map(str,cages)))
      return cages

    return cages[0]

  def getMice(self):
    return frozenset(self.__animalsByName) - self.maskedMice

  def getInmates(self, cage = None):
    if cage == None:
      return frozenset(self.__cages)

    return self.__cages[cage] # is a frozenset already

  def getFirstLick(self, corners = (), mice=()):
    where = self._getMiceClause(mice) + ('licknumber > 0',)
    if isinstance(corners, (int, long)):
      corners = (corners,)

    if len(corners) > 0:
      where += ('visits.corner IN (%s)' % ', '.join(map(str, corners)),)

    res = self.getMaskedSQLSmart('MIN(nosepokes.start)',
                                 ['visits', 'nosepokes'],
                                 where)
    if len(res) == 1:
      return res[0]

  def _getMiceClause(self, mice=None):
    if mice is None or len(mice) == 0:
      mice = ()

    elif isinstance(mice, basestring):
      mice = (mice,)

    miceClause = ()
    if len(mice) > 0:
      mice = tuple(str(self.__mice[x]) for x in mice if x in self.__mice)
      miceClause = ('_aid IN (%s)' % ', '.join(mice),)

    return miceClause

  def getStart(self):
    times = [t for t in [self.maskTimeStart, self.icSessionStart] if t != None]
    if len(times) > 0:
      return max(times)

    return self.getMaskedSQL('visits', 'MIN(start)')[0]

  def getEnd(self):
    times = [t for t in [self.maskTimeEnd, self.icSessionEnd] if t != None]
    if len(times) > 0:
      return min(times)

    return self.getMaskedSQL('visits', 'MAX(start)')[0]


# log analysis
  def _logAnalysis(self, loganalyzers):
    self.excluded = []
    self.loganalyzers = loganalyzers
    for loganalyzer in loganalyzers:
      self.excluded.extend(loganalyzer(self))

  def getExcludedData(self):
    print "WARNING: deprecated method getExcludedData() called."
    return self.getExcluded()

  def getExcluded(self):
    return list(self.excluded)


# masking
  def selectAllData(self, table):
    if table == 'nosepokes':
      fields = [('nosepokes', f) for f in self.structure['nosepokes']]
      aliases = dict(((t, f), f) for (t, f) in fields)
      return self.selectAllDataSmart(('visits', 'nosepokes'),
                                     fields,
                                     aliases)

    else:
      return super(Data, self).selectAllData(table)

# masking
  def unmask_data(self):
    print "WARNING: Deprecated method unmask_data() called"
    return self.unmaskData()

  def unmaskData(self):
    """
    Remove the mask - future queries will not be clipped.
    """
    super(Data, self).unmaskData()
    self.maskedMice = set()
    self.maskedCages = set()
    self.maskTimeStart = None
    self.maskTimeEnd = None

  def _getMask(self, timeStart=None, timeEnd=None):
    mask = super(Data, self)._getMask()
    if timeStart is None:
      timeStart = self.maskTimeStart

    if timeEnd is None:
      timeEnd = self.maskTimeEnd

    if timeStart != None:
      mask += ('visits.start >= %f' % timeStart ,)

    if timeEnd != None:
      mask += ('visits.start < %f' % timeEnd ,)

    if len(self.maskedMice) > 0:
      animals = ('%d' % self.__mice[a] for a in self.maskedMice if a in self.__mice)
      mask += ('visits._aid NOT IN (%s)' % ', '.join(animals) ,)

    if len(self.maskedCages) > 0:
      mask += ('visits.cage NOT IN (%s)' % ', '.join(map(str, self.maskedCages)) ,)

    return mask

  def _getTableMask(self, tables):
    if isinstance(tables, basestring):
      tables = (tables,)

    mask = super(Data, self)._getTableMask(tables)
    for table in tables:
      if table in ('visits', 'nosepokes'):
        if self.maskTimeStart != None:
          mask += ('%s.start >= %f' % (table, self.maskTimeStart) ,)

        if self.maskTimeEnd != None:
          mask += ('%s.start < %f' % (table, self.maskTimeEnd) ,)

      if table == 'visits':
        if len(self.maskedMice) > 0:
          animals = ('%d' % self.__mice[a] for a in self.maskedMice if a in self.__mice)
          mask += ('%s._aid NOT IN (%s)' % (table, ', '.join(animals)) ,)

      if table in ('visits', 'environment', 'HardwareEvents', 'log' ):
        if len(self.maskedCages) > 0:
          mask += ('%s.cage NOT IN (%s)' % (table, ', '.join(map(str, self.maskedCages))) ,)

    return mask

  def mask_data(self, starttime, endtime = None):
    print "WARNING: Deprecated method mask_data() called"
    return self.maskTime(starttime, endtime)

  def maskData(self, starttime, endtime = None):
    print "WARNING: Deprecated method maskData() called"
    return self.maskTime(starttime, endtime)

  def maskTime(self, starttime, endtime = None):
    """
    maskTime(endtime) or maskTime(starttime, endtime)

    All future queries will be clipped to the visits starting between
    starttime and endtime.
    """
    deprecated('time masking would not be supported in the future')
    if endtime == None:
      self.maskTimeEnd = starttime

    else:
      self.maskTimeStart = starttime
      self.maskTimeEnd = endtime

  def maskCage(self, cage):
    self.maskedCages.add(cage)

  def unmaskCage(self, cage):
    self.maskedCages.remove(cage)

  def removeVisits(self, condition="False"):
    self.db.execute('DELETE FROM visits WHERE %s;' % condition)
    self.db.commit()

  def maskAnimal(self, animals=()):
    if isinstance(animals, basestring):
      animals = (animals,)

    animals = set(animals)

    self.maskedMice.update(animals)

    animals = animals - set(self.__mice)
    if len(animals) > 0:
      print 'WARNING, following animals not present in data:'
      for mouse in animals:
        print ' ' + mouse

  def unmaskAnimal(self, animals=()):
    if isinstance(animals, basestring):
      animals = (animals,)

    animals = set(animals)

    self.maskedMice -= set(animals)

    animals = animals - set(self.__mice)
    if len(animals) > 0:
      print 'WARNING, following animals not present in data:'
      for mouse in animals:
        print ' ' + mouse

# data management
  def _insertDataSid(self, data, table, sid = None):
    if isinstance(sid, dict):
      data['_sid'] = [sid[x] for x in data['_sid']]

    elif isinstance(sid, (int, long)):
      key = data.keys()[0]
      n = len(data[key])
      data['_sid'] = [sid] * n

    self.insertData(data, table)

  @staticmethod
  def _newNodes(nodes, cls=None):
    return map(cls.fromDict, nodes)

  def _insertLogs(self, lNodes):
    self.__logs.extend(self._newNodes(lNodes, LogNode)) 

  def _insertEnvironment(self, eNodes):
    self.__environment.extend(self._newNodes(eNodes, EnvironmentNode))

  def _insertHardware(self, hNodes):
    self.__hardware.extend(self._newNodes(hNodes, HardwareEventNode))

  def _insertVisits(self, vNodes):
    vAttributes = self.structure['visits'].keys()
    vFields = map(methodcaller('lower'), vAttributes)
    vAttributes[vAttributes.index('_aid')] = 'Animal._aid'
    assert len(vAttributes) > 1
    vAttributes = attrgetter(*vAttributes)


    assert len(set(vFields)) == len(vFields)
    vQuery = "INSERT INTO visits(%s) VALUES(%s);" % \
             (', '.join(vFields), ', '.join(['?'] * len(vFields)))
    vData = []

    nAttributes = self.structure['nosepokes'].keys() 
    nFields = map(methodcaller('lower'), nAttributes)
    nQuery = "INSERT INTO nosepokes(%s) VALUES(%s);" % \
             (', '.join(nFields), ', '.join(['?'] * len(nFields)))
    nData = []

    if self._getNpokes:
      nAttributes[nAttributes.index('_vid')] = 'Visit._vid'
      assert len(nAttributes) > 1
      nAttributes = attrgetter(*nAttributes)

    vNodes = self._newNodes(vNodes, VisitNode) # callCopy might be faster but requires vNodes to be VisitNode-s
    for (vid, vNode) in enumerate(vNodes, start=len(self.__visits)):
      vNode._vid = vid

      animal = self.getAnimal(vNode.Animal)
      vNode.Animal = animal

      #vNode._aid = animal._aid # a hook
      #vData.append(map(vNode.get, vAttributes))
      vData.append(vAttributes(vNode))

      nosepokes = vNode.pop('Nosepokes', None)
      if self._getNpokes and nosepokes is not None:
        nosepokes = tuple(self._newNodes(nosepokes, NosepokeNode))
        vNode.Nosepokes = nosepokes
        for nid, npNode in enumerate(nosepokes, start=len(self.__nosepokes)):
          npNode.Visit = vNode
          npNode._nid = nid
          #npNode._vid = vid # a hook
          #nData.append(map(npNode.get, nAttributes))
          nData.append(nAttributes(npNode))

        self.__nosepokes.extend(nosepokes)

      else:
        vNode.Nosepokes = None

    self.__insertVisitsDB(vQuery, vData, nQuery, nData)
    self.__visits.extend(vNodes)

  def __insertVisitsDB(self, vQuery, vData, nQuery, nData):
    self.db.executemany(vQuery, vData)
    self.db.executemany(nQuery, nData)
    self.db.commit()

  def _getVisitNode(self, vid):
    return self.getItem(self.__visits, vid)
  
  @staticmethod
  def getItem(collection, key):
    if hasattr(key, '__iter__'):
      if len(key) > 1:
        return itemgetter(*key)(collection)

      if len(key) == 1:
        return (collection[key[0]],)

      return ()

    return collection[key]

  def getGroup(self, name = None):
    if name != None:
      return self.__name2group[name]

    return frozenset(self.__name2group)

  def _registerGroup(self, Name, Animals=[], **kwargs):
    Animals = [self.getAnimal(animal) for animal in Animals] # XXX sanity
    if Name in self.__name2group:
      group = self.__name2group[Name]
      group.merge(Name=Name, Animals=Animals, **kwargs)
      return group

    group = GroupNode(Name=Name, Animals=Animals, **kwargs)
    self.__name2group[Name] = group
    return group

  def _unregisterGroup(self, name):
    del self.__name2group[name]

  def _addMember(self, name, animal):
    group = self.__name2group[name]
    animal = self.getAnimal(animal) # XXX sanity
    group.addMember(animal)

  def getAnimal(self, name = None, aid = None):
    if name is not None:
      return self.__animalsByName[unicode(name)]

    if aid is not None:
      return self.__animals[aid]

    return frozenset(self.__animalsByName)

  def _registerAnimal(self, animal):
    aNode = AnimalNode(animal['Name'], Tag=animal.get('Tag'),
                       Sex=animal.get('Sex'),
                       Notes=animal.get('Notes'))
    return self._registerAnimalNode(aNode)

  def _registerAnimalNode(self, aNode):
    name = aNode.Name
    if name in self.__animalsByName:
      animal = self.__animalsByName[name]
      self._mergeAnimal(animal, **aNode)
      return animal

    aid = len(self.__animals)
    aNode._aid = aid
    self.__animals.append(aNode)
    self.__animalsByName[unicode(name)] = aNode
    return aNode

  def _getAnimalNode(self, aid):
    print "deprecated _getAnimalNode"
    return self.getItem(self.__animals, aid)

  # TODO or not TODO
  def _unregisterAnimal(self, Name = None, aid = None):
    if Name != None:
      animal = self.__animalsByName[unicode(Name)]
      assert aid is None or aid == animal['_aid']
      aid = animal['_aid']

    else:
      animal = self.__animals[aid]
      Name = animal['Name']

    cursor = self.db.execute("SELECT _vid FROM visits WHERE _aid = %d;" % aid)
    vIds = cursor.fetchall()

    for (vid,) in vIds:
      vNode = self.__visits[vid]
      if vNode.Nosepokes:
        for npNode in vNode.Nosepokes:
          self.__nosepokes[npNode._nid] = None # TODO

      vNode._del_()
      self.__visits[vid] = None # TODO

    self.db.executemany("DELETE FROM nosepokes WHERE _vid = ?;", vIds)
    self.db.execute("DELETE FROM visits WHERE _aid = %d;" % aid)
    self.db.commit()

    #del self.__animals[aid]
    self.__animals[aid] = None # TODO
    del self.__animalsByName[Name]
    for group in self.__name2group.values():
      group.delMember(animal)

    animal._del_() # just in case

  def _mergeAnimal(self, animal, **updates):
    updated = animal.merge(**updates)

  def _updateAnimal(self, animal, **updates):
    if len(updates) == 0: return
    assert '_aid' not in updates

    KEY_CACHE = [('Name', self.__animalsByName)]
    errors = []
    for key, cache in KEY_CACHE:
      if key in updates and updates[key] != animal[key] and updates[key] in cache:
        errors.append('%s = %s already registered for other animal!' %\
                      (key, updates[key]))

    if len(errors) > 0:
      raise ValueError('\n'.join(errors))

    for key, cache in KEY_CACHE:
      if key in updates:
        del cache[animal[key]]
        cache[updates[key]] = animal

    for key in updates:
      animal[key] = None

    self._mergeAnimal(animal, **updates)


  # is anyone using it?
  def newGroup(self, group, mice=set()):
    stop
    if group in self.getGroup():
      print "WARNING: Overwriting group %s." % group
      self._unregisterGroup(group)

    self._registerGroup(group)
    for mouse in mice:
      aid = self.getAnimal(mouse)
      aid = aid._aid
      self._addMember(group, aid)

  def getTag(self, mouse):
    tag = self.getAnimal(mouse)
    return tag.Tag

  def getFilteredSQL(self, fields=('*',), mice=None, fromClause='visits', where = (), whereData = (), order=None):
    deprecated("Obsolete method getFilteredSQL() called.",
               PendingDeprecationWarning)
    miceClause = self._getMiceClause(mice)

    if isinstance(where, basestring):
      where = (where,)

    whereData = tuple(whereData)
    whereClause = tuple(where) + miceClause

    return self.getMaskedSQL(fromClause, fields,
                             where = whereClause,
                             whereData = whereData,
                             order = order)

  def getMiceFitterData(self, mice=None):
    deprecated("Obsolete method getMiceFitterData() called.",
               PendingDeprecationWarning)
    return [(v.Animal.Name, v.Start, v.End, v.Corner, v.CornerCondition)\
            for v in self.getVisits(mice=mice, order='start, end')]

  def plotMiceCage(self):
    aids = self.getSQL("""SELECT DISTINCT _aid FROM visits;""")
    for aid in aids:
      mouse = self.__animals[aid].name
      cages = []
      times = []
      data = self.getSQL("""
                         SELECT cage, start
                         FROM visits
                         WHERE _aid = ?
                         ORDER BY start;
                         """,
                         (aid,),
                         unwrap=False)
      lastC, lastT = None, None
      many = False
      for c, t in data:
        if c != lastC:
          if many:
            cages.append(lastC)
            times.append(lastT)

          many = False
          cages.append(c)
          times.append(t)
          lastC = c

        else:
          many = True
          lastT = t

      if many:
        cages.append(lastC)
        times.append(lastT)

      plt.plot(times, cages, label=mouse)

    #plt.legend()

  def plotChannel(self, top=1., bottom=0.):
    #TODO!!!!
    h = top - bottom
    data = self.getSQL("""
                       SELECT MIN(start), MAX(end)
                       FROM visits;
                       """, unwrap=False)
    startD, endD = data[0]
    startR = self.icSessionStart
    endR = self.icSessionEnd
    startM = self.maskTimeStart
    endM = self.maskTimeEnd

    ax = plt.gca()

    if endD is not None and startD is not None: # imagine case when only one is true -_-
      htop = 0.75 * top + 0.25 * bottom
      hbottom = 0.25 * top + 0.75 * bottom
      path = Path([(startD, htop), (endD, htop), (endD, hbottom), (startD, hbottom), (startD, htop)],
                  [Path.MOVETO, Path.LINETO, Path.LINETO, Path.LINETO, Path.CLOSEPOLY])
      patch = patches.PathPatch(path, facecolor='green', edgecolor='green')
      ax.add_patch(patch)

    if startR is not None or endR is not None:
      medium = 0.5 * (top + bottom)
      left = startR if startR is not None else startD if startD is not None else startM
      right = endR if endR is not None else endD if endD is not None else endM
      path = Path([(left, medium), (right, medium)], [Path.MOVETO, Path.LINETO])
      patch = patches.PathPatch(path, facecolor='none', edgecolor='black')
      ax.add_patch(patch)

    if startM is not None or endM is not None:
      verts = []
      codes = []
      left = startM if startM is not None else startR if startR is not None else startD
      right = endM if endM is not None else endR if endR is not None else endD

      codes.append(Path.MOVETO)
      verts.append((left, top))
      codes.append(Path.LINETO)
      verts.append((right, top))
      codes.append(Path.LINETO if endM is not None else Path.MOVETO)
      verts.append((right, bottom))
      codes.append(Path.LINETO)
      verts.append((left, bottom))
      if startM is not None:
        verts.append((left, top))
        codes.append(Path.CLOSEPOLY)

      path = Path(verts, codes)
      patch = patches.PathPatch(path, facecolor='none', edgecolor='red')
      ax.add_patch(patch)

    times = [x for x in [startD, endD, startR, endR, startM, endM] if x is not None]
    return min(times), max(times)

  def plotChannelR(self, top=1., bottom=0.):
    # to be overriden
    return self.plotChannel(top=top, bottom=bottom)

  def getChannel(self, mice=None, corner=None):
    where = self._getMiceClause(mice)
    whereData = ()
    if corner is not None:
      if isinstance(corner, (int, long)):
        whereData += ((corner,),)
        where += ('corner = ?',)

      else:
        whereData += (tuple(corner),)
        where += ('corner IN (%s)' % (', '.join('?' for c in corner)),)

    vids = self.getMaskedSQL('visits', '_vid', where, whereData, 'start, end')
    visits = self._getVisitNode(vids)
    return DataNode(Visits=visits)

  def selectObj(self, kind='visits', mice=None, where = (), whereData = (), order=None,
                timeStart = None, timeEnd=None):
    # mice -> important because of aid-s
    if isinstance(where, basestring):
      where = (where,)

    else:
      where = tuple(where)

    where += self._getMiceClause(mice)

    whereData = tuple(whereData)

    if kind == 'visits':
      vids = self.getMaskedSQL('visits', '_vid', where, whereData, order,
                               timeStart=timeStart,
                               timeEnd=timeEnd)
      return self._getVisitNode(vids)

    else:
      raise NotImplementedError("Unknown kind of objects: %s" % kind)


  def getVisits(self, *args, **kwargs):
    """
    An alias.
    """
    return self.selectObj(kind='visits', *args, **kwargs)

  def __filterDataTimeMask(self, data, timeStart=None, timeEnd=None):
    if timeStart is None:
      timeStart = self.maskTimeStart

    if timeEnd is None:
      timeEnd = self.maskTimeEnd

    if timeStart is not None:
      if timeEnd is not None:
        return [x for x in data if timeStart <= x.DateTime < timeEnd]

      return [x for x in data if timeStart <= x.DateTime]

    if timeEnd is not None:
      return [x for x in data if x.DateTime < timeEnd]

    return list(data)

  def getLogs(self, timeStart=None, timeEnd=None):
    return self.__filterDataTimeMask(self.__logs, timeStart=timeStart, timeEnd=timeEnd)

  def getEnvironment(self, timeStart=None, timeEnd=None):
    return self.__filterDataTimeMask(self.__environment, timeStart=timeStart, timeEnd=timeEnd)

  def getHardwareEvents(self, timeStart=None, timeEnd=None):
    return self.__filterDataTimeMask(self.__hardware, timeStart=timeStart, timeEnd=timeEnd)

  def save(self, filename, force=False):
    if os.path.exists(filename) and not force:
      raise ValueError("File %s already exists." % filename)

    fh = zipfile.ZipFile(filename, 'w')

    # Animals
    buf = cStringIO.StringIO()
    keys = set()
    animals = {}
    for animal in self.__animals:
      keys.update(animal.keys())
      name = unicode(animal)
      assert name not in animals
      animals[name] = str(len(animals))

    keys.discard('_aid')
    keys.discard('Tag')

    keys = list(keys)
    writer = csv.writer(buf, delimiter='\t')
    writer.writerow(['_aid', 'Tag'] + keys)
    for animal in self.__animals:
      _aid = animals[unicode(animal)]
      try:
        tag = animal.Tag
        if isinstance(tag, set):
          tag = ','.join(str(x) for x in sorted(tag))

        else:
          tag = str(tag)

      except:
        tag = ''

      row = animal.select(keys)
      row = [str(x) if x is not None else '' for x in row]
      writer.writerow([_aid, tag] + row)

    fh.writestr('Animals.txt', buf.getvalue(), zipfile.ZIP_DEFLATED)
    buf.reset()
    buf.truncate()

    sources = set()
    logKeys = set()
    envKeys = set()
    visKeys = set()
    npKeys = set()
    visits = {}

    for visit in self.__visits:
      visKeys.update(visit.keys())
      sources.add(visit._source)
      visits[id(visit)] = str(len(visits)) #vid

    for nosepoke in self.__nosepokes:
      npKeys.update(nosepoke.keys())
      sources.add(nosepoke._source)

    for log in self.__logs:
      logKeys.update(log.keys())
      sources.add(log._source)

    for env in self.__environment:
      envKeys.update(env.keys())
      sources.add(env._source)


    sources = [(str(i), src) for (i, src) in enumerate(sorted(sources))]
    writer = csv.writer(buf, delimiter='\t')
    writer.writerow(['_sid', '_source'])
    writer.writerows(sources)
    sources = dict((_source, _sid) for (_sid, _source) in sources)

    fh.writestr('_Sources.txt', buf.getvalue(), zipfile.ZIP_DEFLATED)
    buf.reset()
    buf.truncate()

    if visKeys:
      visKeys.remove('Animal')
      visKeys.remove('Start')
      visKeys.remove('End')
      visKeys.remove('_source')
      visKeys.discard('Nosepokes')
      visKeys.remove('_vid')
      visKeys = list(visKeys)

      writer = csv.writer(buf, delimiter='\t')
      writer.writerow(['_vid', '_aid', 'Start', 'End'] + visKeys + ['_sid'])
      for visit in self.__visits:
        _vid = visits[id(visit)]
        _aid = animals[unicode(visit.Animal)]
        Start = timeString(visit.Start)
        End = timeString(visit.End)
        _sid = sources[visit._source]
        row = visit.select(visKeys)
        row = [_vid, _aid, Start, End] +\
              [str(x) if x is not None else '' for x in row] +\
              [_sid]
        writer.writerow(row)

      fh.writestr('IntelliCage/Visits.txt', buf.getvalue(), zipfile.ZIP_DEFLATED)
      buf.reset()
      buf.truncate()

    if npKeys:
      npKeys.remove('_nid')
      npKeys.remove('_source')
      npKeys.remove('Visit')
      npKeys.remove('Start')
      npKeys.remove('End')
      npKeys = list(npKeys)

      writer = csv.writer(buf, delimiter='\t')
      writer.writerow(['_vid', 'Start', 'End'] + visKeys + ['_sid'])
      for nosepoke in self.__nosepokes:
        try:
          _vid = visits[id(nosepoke.Visit)]

        except:
          _vid = ''

        Start = timeString(nosepoke.Start)
        End = timeString(nosepoke.End)
        _sid = sources[nosepoke._source]
        row = nosepoke.select(npKeys)
        row = [_vid, Start, End] +\
              [str(x) if x is not None else '' for x in row] +\
              [_sid]
        writer.writerow(row)

      fh.writestr('IntelliCage/Nosepokes.txt', buf.getvalue(), zipfile.ZIP_DEFLATED)
      buf.reset()
      buf.truncate()

    if logKeys:
      logKeys.remove('_source')
      logKeys.remove('DateTime')
      logKeys = list(logKeys)

      writer = csv.writer(buf, delimiter='\t')
      writer.writerow(['DateTime'] + visKeys + ['_sid'])
      for log in self.__logs:
        _sid = sources[log._source]
        DateTime = timeString(log.DateTime)
        row = log.select(logKeys)
        row = [DateTime] + row + [_sid]
        writer.writerow(row)

      fh.writestr('IntelliCage/Log.txt', buf.getvalue(), zipfile.ZIP_DEFLATED)
      buf.reset()
      buf.truncate()

    if envKeys:
      envKeys.remove('_source')
      envKeys.remove('DateTime')
      envKeys = list(envKeys)

      writer = csv.writer(buf, delimiter='\t')
      writer.writerow(['DateTime'] + visKeys + ['_sid'])
      for env in self.__environment:
        _sid = sources[env._source]
        DateTime = timeString(env.DateTime)
        row = env.select(logKeys)
        row = [DateTime] + row + [_sid]
        writer.writerow(row)

      fh.writestr('IntelliCage/Environment.txt', buf.getvalue(), zipfile.ZIP_DEFLATED)
      buf.reset()
      buf.truncate()

    fh.close()

if __name__ == '__main__':
  import doctest
  try:
    from _test import TEST_GLOBALS

  except ImportError:
    print "from _test import... failed"
    from Mice._test import TEST_GLOBALS

  doctest.testmod(extraglobs=TEST_GLOBALS)
