#!/usr/bin/env python
# encoding: utf-8
###############################################################################
#                                                                             #
#    PyMICE library                                                           #
#                                                                             #
#    Copyright (C) 2012-2020 Jakub M. Dzik a.k.a. Kowalski, S. Łęski          #
#    (Laboratory of Neuroinformatics; Nencki Institute of Experimental        #
#    Biology of Polish Academy of Sciences)                                   #
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

# original: 2.7% (1.8 GB max); 73s
# rewritten: 0.6% (412 MB max); 73s

import sys
if sys.version_info >= (3, 0):
  unicode = str

import os
import csv
import warnings
import logging

try:
  import cStringIO as io

except ImportError:
  import io

import dateutil.parser
import pytz

from xml.dom import minidom

from operator import methodcaller, attrgetter, itemgetter
try:
  from itertools import izip, repeat, count, chain

except ImportError:
  from itertools import repeat, count, chain
  izip = zip

from datetime import datetime, timedelta, timezone, MINYEAR

from .Data import Data
from .ICNodes import (Animal, Visit, Nosepoke, LogEntry,
                      EnvironmentalConditions, AirHardwareEvent,
                      DoorHardwareEvent, LedHardwareEvent,
                      UnknownHardwareEvent, Session)

from ._Tools import (timeToList, ArchiveZipFile, DirectoryZipFile, warn, groupBy,
                     isString, mapAsList, MissingIdentityDict, AdditiveDict)
from ._Analysis import Aggregator

# dependence tracking
from . import _dependencies, Data as _Data, ICNodes, _Tools, _Analysis
import dateutil
import types
__dependencies__ = _dependencies.moduleDependencies(*[x for x in globals().values()
                                                      if isinstance(x, types.ModuleType)])


class PmCImportWarning(ImportWarning):
  pass

try:
  from pymice._cpymice import emptyStringToNone

except Exception as e:
  warnings.warn('%s\t%s' % (type(e), e),
                PmCImportWarning)

  def emptyStringToNone(l):
    for i, x in enumerate(l):
      if type(x) is list:
        emptyStringToNone(x)

      elif x == '':
        l[i] = None

    return l


logger = logging.getLogger(__name__)


convertFloat = methodcaller('replace', ',', '.')


_LOG_ENV_HW = ["Log", "Env", "Hw"]


class Loader(Data):
  _legacy = {'Animals': {'Name': 'AnimalName',
                         'Tag': 'AnimalTag',
                         'Group': 'GroupName',
                         'Notes': 'AnimalNotes',
                        },
             'Visits': {'Animal': 'AnimalTag',
                        'ID': 'VisitID',
                        'Module': 'ModuleName',
                       },
             'Nosepokes': {'LicksNumber': 'LickNumber',
                           'LicksDuration': 'LickDuration',
                          },
             'Log': {'Type': 'LogType',
                     'Time': 'DateTime',
                     'Category': 'LogCategory',
                     'Notes': 'LogNotes',
                    },
             'HardwareEvents': {'Type': 'HardwareType',
                                'Time': 'DateTime',
                               },
             'Environment': {'Time': 'DateTime',
                             }
            }

  _convertZip = {'Animals': {#'Tag': int,
                            },
                 'Visits': {#'Tag': int,
                            #'_vid': int,
                            'Start': timeToList,
                            'End': timeToList,
                            'CornerCondition': convertFloat,
                            'PlaceError': convertFloat,
                            'AntennaDuration': convertFloat,
                            'PresenceDuration': convertFloat,
                            },
                 'Nosepokes': {#'_vid': int,
                               'Start': timeToList,
                               'End': timeToList,
                               'LickContactTime': convertFloat,
                               'LickDuration': convertFloat,
                               'SideCondition': convertFloat,
                               'SideError': convertFloat,
                               'TimeError': convertFloat,
                               'ConditionError': convertFloat,
                               'LickStartTime': timeToList,
                               },
                 'Log': {'DateTime': timeToList,
                         'Time':timeToList,
                         },
                 'Environment': {'DateTime': timeToList,
                                 'Temperature': convertFloat,
                                 'Time':timeToList,
                                 },
                 'HardwareEvents': {'DateTime': timeToList,
                                    'Time':timeToList,
                                    },
                }

  __optionalTables = ["Np"] + _LOG_ENV_HW

  def __init__(self, fname, getNp=True, getLog=False, getEnv=False, getHw=False,
               verbose=False, **kwargs):
    """
    :param fname: a path to the data file.
    :type fname: basestring

    :param getNp: whether to load nosepoke data.
    :type getNp: bool

    :param getLog: whether to load log.
    :type getLog: bool

    :param getEnv: whether to load environmental data.
    :type getEnv: bool

    :param getHw: whether to load hardware data.
    :type getHw: bool

    :param verbose: whether to output verbose messages
    :type verbose: bool
    """
    for key, value in kwargs.items():
      warn.warn("Unknown argument %s given for Loader constructor." % key, stacklevel=2)

    Data.__init__(self, getNp=getNp, getLog=getLog, getEnv=getEnv, getHw=getHw)
    self._setCageManager(ICCageManager())
    self.__verbose = verbose

    self._fnames = (fname,)

    self._loadData(fname)

    self._setIcSessionAttributes()
    self.freeze()


  def _loadData(self, fname):
    self.__reportDataLoading(fname)

    if fname.endswith('.zip') or os.path.isdir(fname):
      zf = self._openData(fname)

      self._load(zf, source=fname)

    self._buildCache()

  def _openData(self, fname):
    if isString(fname) and os.path.isdir(fname):
      zf = DirectoryZipFile(fname)

    else:
      zf = ArchiveZipFile(fname)
    return zf

  def __reportDataLoading(self, fname):
    if self.__verbose:
      if isinstance(fname, str):  # XXX: Python3
        print('loading data from {}'.format(fname))

      else:
        print('loading data from {}'.format(fname.encode('utf-8')))

  def _load(self, zf, source=None):
    loader = self.__getLoader(zf, source)

    tables = self.__getTables(zf, source, loader)
    self.__warnAboutOrphanedNosepokes(tables, loader)
    self.__makeDatetimeFieldsTimezoneAware(tables, loader, zf)
    self._insertNewVisits(loader.wrapVisits(tables["Visits"],
                                            tables.get("Np")))
    self.__insertLogEnvHw(tables, loader)

  def __getLoader(self, zf, source):
    ZipLoader = self._getZipLoaderClass(zf)
    self._loadAnimals(zf, ZipLoader)
    return ZipLoader(source,
                     self._cageManager,
                     self._makeTagToAnimalDict())

  def __getTables(self, zf, source, loader):
    return (AdditiveDict(
              Visits=self._fromZipCSV(zf,
                                      loader.KEY_TO_STEM["Visits"],
                                      source=source))
            + self.__getOptionalTables(zf, source, loader))

  def __warnAboutOrphanedNosepokes(self, tables, loader):
    try:
      nosepokes = tables["Np"]

    except KeyError:
      return

    visits = tables["Visits"]
    vids = set(visits[loader.VISIT_ID_FIELD])

    for vid in nosepokes['VisitID']:
      if vid not in vids:
        warn.warn("Orphaned nosepoke with VisitID = {}".format(vid))

  def __insertLogEnvHw(self, tables, loader):
    for name in _LOG_ENV_HW:
      self.__tryToInsertTable(tables, name, loader)

  def __tryToInsertTable(self, tables, name, loader):
    try:
      table = tables[name]

    except KeyError:
      return

    getattr(self, "_insertNew" + name)(getattr(loader, "wrap" + name)(table))

  def __getOptionalTables(self, zf, source, loader):
    for name in self.__optionalTables:
      table = self.__tryToLoadTableIfRequested(name,
                                               zf,
                                               source,
                                               loader)
      if table is not None:
        yield name, table

  def __tryToLoadTableIfRequested(self, name, zf, source, loader):
    if self._requested(name):
      try:
        return self._fromZipCSV(zf,
                                loader.KEY_TO_STEM[name],
                                source=source)

      except KeyError:
        pass

  def _requested(self, name):
    return getattr(self, "_get" + name)

  def __makeDatetimeFieldsTimezoneAware(self, tables, loader, zf):
    tzinfo = self.__get_timezone(loader, zf)
    for t in self.__extractDatetimeFields(tables, loader):
      if t is not None:
        t.append(tzinfo)
    self.__convertNecessaryFieldsToDatetime(tables, loader)

  def __extractDatetimeFields(self, tables, loader):
    datetimes = [table[column]
                 for name, table in tables.items()
                 for column in loader.DATETIME_FIELDS[name]]

    return chain(*datetimes)

  def __get_timezone(self, loader, zf):
    sessions = loader.extractSessions(zf)
    if sessions is None:
      return pytz.utc  # UTC assumed

    assert len(sessions) == 1
    session = sessions[0]
    return session.Start.tzinfo

  def __convertNecessaryFieldsToDatetime(self, tables, loader):
    for name, table in tables.items():
      for column in loader.DATETIME_FIELDS[name]:
        self.__convertFieldToDatetime(column, table)

  def __convertFieldToDatetime(self, field, table):
    table[field] = [datetime(*x) if x is not None else x for x in table[field]]

  def _getZipLoaderClass(self, zf):
    try:
      version = self._checkVersion(zf)

    except Exception as e:
      logger.warning('{} occured when checking version.  Assuming IC+ v. 3'.format(e))
      return ZipLoader_v_IntelliCage_Plus_3

    try:
      return ZIP_LOADERS[version]

    except KeyError:
      logger.warning('Unknown version: {}.  Using loader for IC+ v. 3'.format(version))
      return ZipLoader_v_IntelliCage_Plus_3_1


  def _checkVersion(self, zf):
    with self._findAndOpenZipFile(zf, 'DataDescriptor.xml') as fh:
      dom = minidom.parse(fh)

    dd = dom.getElementsByTagName('DataDescriptor')[0]
    version = dd.getElementsByTagName('Version')[0]
    versionStr = version.childNodes[0]
    assert versionStr.nodeType == versionStr.TEXT_NODE
    return versionStr.nodeValue.strip().lower()

  def _fromZipCSV(self, zf, path, source=None):
    with self._findAndOpenZipFile(zf, path + '.txt') as fh:
      return self._fromCSV(fh,
                           source=source,
                           convert=self._convertZip.get(path))

  @staticmethod
  def _findAndOpenZipFile(zf, path):
    return _ZipLoaderBase._findAndOpenZipFile(zf, path)

  def _fromCSV(self, fh, source=None, convert=None):
    return self.__fromCSV(list(csv.reader(fh, delimiter='\t')),
                          source,
                          convert)

  def __fromCSV(self, data, source, convert):
    if len(data) == 0:
      return None

    labels = data.pop(0)

    n = len(data)
    if n == 0:
      return {l: [] for l in labels}

    emptyStringToNone(data)
    return self.__DictOfColumns(labels, data, source, convert)

  class __DictOfColumns(dict):
    def __init__(self, labels, rows, source, conversions):
      dict.__init__(self, zip(labels, zip(*rows)))
      self.__rowCount = len(rows)

      if source is not None:
        self.__appendDebugInformation(source)

      if conversions is not None:
        self.__convertCollumns(conversions)

    def __appendDebugInformation(self, source):
      assert '_source' not in self
      self['_source'] = [source] * self.__rowCount

      assert '_line' not in self
      self['_line'] = range(1, self.__rowCount + 1)

    def __convertCollumns(self, conversions):
      for label, f in conversions.items():
        if label in self:
          self[label] = mapAsList(f, self[label])


  def _setIcSessionAttributes(self):
    for log in self.getLog():
      if log.Category != 'Info' or log.Type != 'Application':
        continue

      if log.Notes == 'Session is started':
        self.icSessionStart = log.DateTime

      elif log.Notes == 'Session is stopped':
        self.icSessionEnd = log.DateTime

      else:
        print('unknown Info/Application message: {0.Notes}'.format(log))

  def __repr__ (self):
    """
    Nice string representation for prtinting this class.
    """
    mystring = 'IntelliCage data loaded from: %s' %\
               self._fnames.__str__()
    return mystring

  def _loadAnimals(self, zf, loader):
    animalData = self._fromZipCSV(zf, 'Animals')

    animals = loader.extractAndWrapAnimals(animalData)

    for animal in animals:
      self._registerAnimal(animal)

    groups = loader.extractAndWrapGroups(animalData)
    for name in groups:
      if name is not None:
        self._registerGroup(name, groups[name])

  def _makeTagToAnimalDict(self):
    animals = [self.getAnimal(a) for a in self.getAnimal()]
    tagToAnimal = {t: a for a in animals for t in a.Tag}
    assert len(animals) == len(tagToAnimal)
    assert len(set(tagToAnimal.values())) == len(tagToAnimal)
    return tagToAnimal


class Merger(Data):
  """
  >>> mm = Merger(ml_icp3, ml_l1)
  >>> for v in mm.getVisits(order='Start'):
  ...   print('%s %d %s' % (str(v.Animal), len(v.Nosepokes), list(v.Animal.Tag)[0]))
  Minnie 0 1337
  Mickey 1 42
  Jerry 2 69
  Minnie 1 1337
  Mickey 1 42
  Jerry 2 69

  >>> mm = Merger(ml_empty, ml_l1)
  >>> for v in mm.getVisits(order='Start'):
  ...   print('%s %d' % (str(v.Animal), len(v.Nosepokes)))
  Minnie 1
  Mickey 1
  Jerry 2

  >>> mm = Merger(ml_retagged, ml_l1)
  >>> for v in mm.getVisits(order='Start'):
  ...   print('%s %d' % (str(v.Animal), len(v.Nosepokes)))
  ...   print("  %s" % (', '.join(sorted(v.Animal.Tag))))
  Mickey 0
    1337, 42
  Minnie 1
    1337, 42
  Jerry 2
    69
  Minnie 1
    1337, 42
  Mickey 1
    1337, 42
  Jerry 2
    69
  """
  def __init__(self, *dataSources, **kwargs):
    """
    Usage: Merger(data_1, [data_2, ...] [parameters])

    :arg dataSources: objects containing IntelliCage data
    :type dataSources: [:py:class:`Data`, ...]

    :keyword getNp: whether to load nosepoke data (defaults to False).
    :type getNp: bool

    :keyword getLog: whether to load log (defaults to False).
    :type getLog: bool

    :keyword getEnv: whether to load environmental data (defaults to False).
    :type getEnv: bool

    :keyword getHw: whether to load hardware data (defaults to False).
    :type getHw: bool

    :keyword ignoreMiceDifferences: whether to ignore encountered differences
                                    in animal description (e.g. sex)
    :type ignoreMiceDifferences: bool
    """
    getNp = kwargs.pop('getNp', True)
    getLog = kwargs.pop('getLog', False)
    getEnv = kwargs.pop('getEnv', False)
    getHw = kwargs.pop('getHw', False)

    self._ignoreMiceDifferences = kwargs.pop('ignoreMiceDifferences', False)

    for key, value in kwargs.items():
      warn.warn("Unknown argument %s given for Merger constructor" % key,
                stacklevel=2)

    Data.__init__(self, getNp=getNp, getLog=getLog, getEnv=getEnv, getHw=getHw)
    self._setCageManager(ICCageManager())

    self._dataSources = map(str, dataSources)

    self.__topTime = datetime(MINYEAR, 1, 1, tzinfo=pytz.timezone('Etc/GMT-14'))

    for dataSource in self._sortDataSources(dataSources):
      try:
        self._appendDataSource(dataSource)

      except:
        print("ERROR processing {}".format(dataSource))
        raise

    self.freeze()


  @staticmethod
  def _sortDataSources(dataSources):
    """
    >>> class FakeData(object):
    ...   def __init__(self, start=None):
    ...     self.__start = start
    ...   def getStart(self):
    ...     return self.__start
    >>> dtA = datetime(2012, 2, 1)
    >>> dtB = datetime(2012, 2, 2)

    >>> list(map(methodcaller('getStart'),
    ...          Merger._sortDataSources([FakeData(), FakeData(dtA),
    ...                                   FakeData(dtB), FakeData(dtA)]))) == [dtA, dtA, dtB, None]
    True

    >>> list(map(methodcaller('getStart'),
    ...          Merger._sortDataSources([FakeData(dtA),
    ...                                   FakeData(dtB), FakeData(dtA)]))) == [dtA, dtA, dtB]
    True

    >>> list(map(methodcaller('getStart'),
    ...          Merger._sortDataSources([FakeData(), FakeData(), FakeData()]))) == [None, None, None]
    True
    """
    sourcesByStartPresence = groupBy(dataSources, getKey=lambda x: x.getStart() is not None)
    return sorted(sourcesByStartPresence.get(True, []), key=methodcaller('getStart')) \
           + sourcesByStartPresence.get(False, [])

  def __repr__(self):
    mystring = 'IntelliCage data loaded from: %s' %\
                str(self._dataSources)
    return mystring

  def _appendDataSource(self, dataSource):
    if dataSource.icSessionStart != None:
      if self.icSessionStart != None and self.icSessionEnd != None:
        if self.icSessionStart < dataSource.icSessionStart\
          and self.icSessionEnd > dataSource.icSessionStart:
          print('Overlap of IC sessions detected')

    if dataSource.icSessionEnd != None:
      if self.icSessionStart != None and self.icSessionEnd != None:
        if self.icSessionStart < dataSource.icSessionEnd\
          and self.icSessionEnd > dataSource.icSessionEnd:
          print('Overlap of IC sessions detected')

    # TODO: overlap issue!
    for attr, choice in [('Start', min),
                         ('End', max)]:
      icAttr = 'icSession' + attr
      vals = [x for x in [getattr(self, icAttr),
                          getattr(dataSource, 'get' + attr)()] if x is not None]
      if len(vals) > 0:
        setattr(self, icAttr, choice(vals))

    # registering animals and groups (if necessary)
    for name in dataSource.getAnimal():
      animal = dataSource.getAnimal(name)
      try:
        self._registerAnimal(animal)

      except Animal.DifferentMouseError:
        if not self._ignoreMiceDifferences:
          raise


    for group in dataSource.getGroup():
      gData = dataSource.getGroup(group)
      self._registerGroup(**gData)

    visits = dataSource.getVisits()

    if visits != None:
      try:
        minStart = min(v.Start for v in visits)

      except ValueError:
        pass

      else:
        if minStart < self.__topTime:
          print("Possible temporal overlap of visits")

      self.insertVisits(visits)

    if self._getHw:
      hardware = dataSource.getHardwareEvents()
      if hardware is not None:
        self.insertHw(hardware)

    if self._getEnv:
      env = dataSource.getEnvironment()
      if env is not None:
        self.insertEnv(env)

    if self._getLog:
      log = dataSource.getLog()
      if log is not None:
        self.insertLog(log)

    ## XXX more data loading here

    if visits != None:
      maxEnd = [self.__topTime]
      maxEnd.extend(v.End for v in visits)
      if self._getNp:
        maxEnd.extend(n.End for v in visits if v.Nosepokes for n in v.Nosepokes)

      self.__topTime = max(maxEnd)

    if self._getHw and hardware:
      self.__topTime = max(self.__topTime, max(hw.DateTime for hw in hardware))

    if self._getEnv and env:
      self.__topTime = max(self.__topTime, max(en.DateTime for en in env))

    if self._getLog and log:
      self.__topTime = max(self.__topTime, max(l.DateTime for l in log))

    self._buildCache()


class ICSide(int):
  #__slots__ = ('__Corner',)
  def __setattr__(self, key, value):
    if key == '_ICSide__Corner':
      self.__dict__[key] = value

    else:
      raise AttributeError(key)

  def __new__(cls, value, corner):
    obj = int.__new__(cls, value)
    obj.__Corner = corner
    return obj

  def _del_(self):
    del self.__Corner

  @property
  def Corner(self):
    return self.__Corner


class ICCorner(int):
  class NoSideError(KeyError):
    pass

  #__slots__ = ('__Cage', '__sides', '__sideMapping')
  def __setattr__(self, key, value):
    if key in ('_ICCorner__Cage', '_ICCorner__sides', '_ICCorner__sideMapping'):
      self.__dict__[key] = value

    else:
      raise AttributeError(key)

  def __new__(cls, value, cage):
    obj = int.__new__(cls, value)
    obj.__Cage = cage

    obj.__sides = []
    obj.__sideMapping = {}

    for i, s in enumerate(['left', 'right'], obj * 2 - 1):
      side = ICSide(i, obj)
      obj.__sides.append(side)
      obj.__sideMapping[i] = side
      obj.__sideMapping[str(i)] = side
      obj.__sideMapping[s] = side

    return obj

  def __getitem__(self, side):
    try:
      return self.__sideMapping[side]

    except KeyError:
      raise self.NoSideError(side)

  def _del_(self):
    for side in self.__sides:
      side._del_()

    del self.__Cage

  @property
  def Cage(self):
    return self.__Cage

  Left = property(itemgetter('left'))
  Right = property(itemgetter('right'))


class ICCage(int):
  class NoCornerError(KeyError):
    pass

  #__slots__ = ('__corners', '__cornerMapping')
  def __setattr__(self, key, value):
    if key in ('_ICCage__corners', '_ICCage__cornerMapping'):
      self.__dict__[key] = value

    else:
      raise AttributeError(key)

  def __init__(self, _):
    self.__corners = [ICCorner(i, self) for i in range(1, 5)]
    self.__cornerMapping = {}
    for corner in self.__corners:
      self.__cornerMapping[corner] = corner
      self.__cornerMapping[str(corner)] = corner

  def __getitem__(self, corner):
    try:
      return self.__cornerMapping[corner]

    except KeyError:
      raise self.NoCornerError(corner)

  def _del_(self):
    for corner in self.__corners:
      corner._del_()


class ICCageManager(object):
  __slots__ = ('__cageMapping', '__cages')

  def __init__(self):
    self.__cageMapping = {}
    self.__cages = []

  def __getitem__(self, cage):
    try:
      return self.__cageMapping[cage]

    except KeyError:
      item = ICCage(cage)
      self.__cages.append(item)
      self.__cageMapping[int(cage)] = item
      self.__cageMapping[str(cage)] = item
      return item

  def _del_(self):
    for cage in self.__cages:
      cage._del_()


class _ZipLoaderBase(object):
  KEY_TO_STEM = MissingIdentityDict(
    Np="Nosepokes",
    Hw="HardwareEvents",
    Env="Environment")

  DATETIME_FIELDS = AdditiveDict(
    Visits=["Start", "End"],
    Np=["Start", "End"])

  def __init__(self, source, cageManager, animalManager):
    self.__animalManager = animalManager
    self._cageManager = cageManager
    self._source = source

  def _makeVisit(self, Cage, Corner, AnimalTag, Start, End, ModuleName,
                 CornerCondition, PlaceError,
                 AntennaNumber, AntennaDuration, PresenceNumber, PresenceDuration,
                 VisitSolution, _line, _id, nosepokeRows):
    animal = self.__animalManager[AnimalTag]
    cage = self._cageManager[Cage]
    corner = cage[Corner]

    Nosepokes = None
    if nosepokeRows is not None:
      Nosepokes = tuple(self._makeNosepoke(corner, row)\
                        for row in sorted(nosepokeRows))

    return Visit(Start, corner, animal, End,
                 unicode(ModuleName) if ModuleName is not None else None,
                 cage,
                 int(CornerCondition) if CornerCondition is not None else None,
                 int(PlaceError) if PlaceError is not None else None,
                 int(AntennaNumber) if AntennaNumber is not None else None,
                 timedelta(seconds=float(AntennaDuration)) if AntennaDuration is not None else None,
                 int(PresenceNumber) if PresenceNumber is not None else None,
                 timedelta(seconds=float(PresenceDuration)) if PresenceDuration is not None else None,
                 int(VisitSolution) if VisitSolution is not None else None,
                 self._source, _line, _id,
                 Nosepokes)

  def _makeNosepoke(self, sideManager, nosepokeTuple):
    (Start, End, Side,
     SideCondition, SideError, TimeError, ConditionError,
     LickNumber, LickContactTime, LickDuration,
     AirState, DoorState, LED1State, LED2State, LED3State,
     LickStartTime,
     _line) = nosepokeTuple
    return Nosepoke(Start, End,
                    sideManager[Side] if Side is not None else None,
                    int(LickNumber) if LickNumber is not None else None,
                    timedelta(seconds=float(LickContactTime)) if LickContactTime is not None else None,
                    timedelta(seconds=float(LickDuration)) if LickDuration is not None else None,
                    int(SideCondition) if SideCondition is not None else None,
                    int(SideError) if SideError is not None else None,
                    int(TimeError) if TimeError is not None else None,
                    int(ConditionError) if ConditionError is not None else None,
                    int(AirState) if AirState is not None else None,
                    int(DoorState) if DoorState is not None else None,
                    int(LED1State) if LED1State is not None else None,
                    int(LED2State) if LED2State is not None else None,
                    int(LED3State) if LED3State is not None else None,
                    LickStartTime if LickStartTime is not None else None,
                    self._source, _line)

  def wrapVisits(self, visitsCollumns, nosepokesCollumns=None):
    vIDs = visitsCollumns[self.VISIT_ID_FIELD]
    if nosepokesCollumns is not None:
      vNosepokes = self._assignNosepokesToVisits(nosepokesCollumns,
                                                 vIDs)

    else:
      vNosepokes = repeat(None)

    vColValues = [visitsCollumns.get(x, repeat(None)) \
                  for x in self.VISIT_FIELDS]
    vLines = count(1)
    vColValues.append(vLines)
    vColValues.append(map(int, vIDs))
    vColValues.append(vNosepokes)
    return mapAsList(self._makeVisit, *vColValues)

  def _assignNosepokesToVisits(self, nosepokesCollumns, vIDs):
    vNosepokes = [[] for _ in vIDs]
    vidToNosepokes = dict(izip(vIDs, vNosepokes))

    nColValues = [nosepokesCollumns.get(x, repeat(None)) \
                  for x in self.NOSEPOKE_FIELDS]
    nIDs = nosepokesCollumns['VisitID']
    nRows = len(nIDs)
    nLines = range(1, 1 + nRows)
    nColValues.append(nLines)

    for vId, row in izip(nIDs, izip(*nColValues)):
      vidToNosepokes[vId].append(row)

    return vNosepokes

  @classmethod
  def _columnsToObjects(cls, columns, columnNames, objectFactory):
    colValues = cls._getColumnValues(columnNames, columns)
    return mapAsList(objectFactory, *colValues)

  def _makeLog(self, DateTime, Category, Type,
               Cage, Corner, Side, Notes, _line):
    cage, corner, side = self._getLogCageCornerSide(Cage, Corner, Side)

    return LogEntry(DateTime, unicode(Category), unicode(Type),
                    cage, corner, side,
                    unicode(Notes) if Notes is not None else None,
                    self._source,
                    _line)

  def _getLogCageCornerSide(self, Cage, Corner, Side):
    return self._getCageCornerSide(Cage, Corner, Side)

  @classmethod
  def group(cls, objects, group):
    return Aggregator.aggregate(zip(objects, group),
                                getKey=lambda x: x[1],
                                aggregateFunction=lambda xs: {x[0] for x in xs})

  @staticmethod
  def _makeAnimal(Name, Tag, Sex, Notes, _line):
    return Animal.fromRow(Name, Tag, Sex, Notes)

  @staticmethod
  def _getColumnValues(columnNames, columns):
    return [columns.get(c) for c in columnNames] + [count(1)]

  def _makeHw(self, DateTime, Type, Cage, Corner, Side, State, _line):
    cage, corner, side = self._getHwCageCornerSide(Cage, Corner, Side)

    try:
      return self._hwClass[Type](DateTime, cage, corner, side,
                                 int(State), self._source, _line)

    except KeyError:
      return UnknownHardwareEvent(DateTime, int(Type), cage, corner, side,
                                  int(State), self._source, _line)

  def _getHwCageCornerSide(self, Cage, Corner, Side):
    return self._getCageCornerSide(Cage, Corner, Side)

  _hwClass = {'0': AirHardwareEvent,
              '1': DoorHardwareEvent,
              '2': LedHardwareEvent,
              }

  def _getCageCornerSide(self, Cage, Corner, Side):
    if Cage is None:
      return Cage, Corner, Side

    cage = self._cageManager[Cage]
    if Corner is None:
      return cage, Corner, Side

    corner = cage[Corner]
    if Side is None:
      return cage, corner, Side

    return cage, corner, corner[Side]

  @staticmethod
  def _findAndOpenZipFile(zf, path):
    try:
      return zf.open(path)

    except KeyError:
      return zf.open('IntelliCage/' + path)

  def extractSessions(self, zf):
    try:
      with self._findAndOpenZipFile(zf, 'Sessions.xml') as fh:
        dom = minidom.parse(fh)

      aos = dom.getElementsByTagName('ArrayOfSession')[0]
      ss = aos.getElementsByTagName('Session')
      sessions = []
      for session in ss:
        start, end = self._extract_session_time_bounds(session)

        if end is not None and start.tzinfo != end.tzinfo:
          warn.warn(UserWarning('Timezone changed!'))

        for sessionStart, sessionEnd in sessions:
          if sessionEnd is None:
            continue

          if sessionStart < start < sessionEnd or \
                  end is not None and sessionStart < end < sessionEnd or \
                  (end is not None and start <= sessionStart and sessionEnd <= end) or \
                  (end is not None and sessionStart <= start and end <= sessionEnd):
            warn.warn(UserWarning('Temporal overlap of sessions!'))

        sessions.append(Session(Start=start, End=end))

      sessions = sorted(sessions, key=attrgetter('Start'))

    except:
      sessions = None

    return sessions

  def _extract_session_time_bounds(self, session):
    interval = session.getElementsByTagName('Interval')[0]
    start = interval.getElementsByTagName('Start')[0]
    start = start.childNodes[0]
    assert start.nodeType == start.TEXT_NODE
    start = dateutil.parser.parse(start.nodeValue)

    end = interval.getElementsByTagName('End')[0]
    end = end.childNodes[0]
    assert end.nodeType == end.TEXT_NODE
    end = end.nodeValue
    end = None if end.startswith('0001') else dateutil.parser.parse(end)
    return start, end


class ZipLoader_v_IntelliCage_Plus_3(_ZipLoaderBase):
  DATETIME_FIELDS = (_ZipLoaderBase.DATETIME_FIELDS
                     + {k: ["DateTime"] for k in _LOG_ENV_HW})

  VISIT_FIELDS = ['Cage', 'Corner',
                  'AnimalTag', 'Start', 'End', 'ModuleName',
                  'CornerCondition', 'PlaceError',
                  'AntennaNumber', 'AntennaDuration',
                  'PresenceNumber', 'PresenceDuration',
                  'VisitSolution',
                  ]
  VISIT_ID_FIELD = 'VisitID'
  VISIT_TAG_FIELD = 'AnimalTag'

  NOSEPOKE_FIELDS = ['Start', 'End', 'Side',
                     'SideCondition', 'SideError',
                     'TimeError', 'ConditionError',
                     'LickNumber', 'LickContactTime',
                     'LickDuration',
                     'AirState', 'DoorState',
                     'LED1State', 'LED2State',
                     'LED3State',
                     'LickStartTime',  # Only IC+ v. 3.1
                     ]

  def wrapLog(self, columns):
    return self._columnsToObjects(columns,
                                  ['DateTime',
                                   'LogCategory',
                                   'LogType',
                                   'Cage',
                                   'Corner',
                                   'Side',
                                   'LogNotes'],
                                  self._makeLog)

  def _makeEnv(self, DateTime, Temperature, Illumination, Cage,
               _line):
    return EnvironmentalConditions(DateTime,
                                   float(Temperature),
                                   int(Illumination),
                                   self._cageManager[Cage] if Cage is not None else None,
                                   self._source, _line)

  def wrapEnv(self, columns):
    return self._columnsToObjects(columns,
                                  ['DateTime', 'Temperature',
                                   'Illumination', 'Cage'],
                                  self._makeEnv)

  def wrapHw(self, columns):
    return self._columnsToObjects(columns,
                                  ['DateTime',
                                   'HardwareType',
                                   'Cage',
                                   'Corner',
                                   'Side',
                                   'State'],
                                  self._makeHw)

  @classmethod
  def extractAndWrapAnimals(cls, columns):
    return cls._columnsToObjects(columns,
                                 ['AnimalName', 'AnimalTag','Sex',
                                  'AnimalNotes'],
                                 cls._makeAnimal)

  @classmethod
  def extractAndWrapGroups(cls, columns):
    return cls.group(columns['AnimalName'],
                     columns['GroupName'])


class ZipLoader_v_IntelliCage_Plus_3_1(ZipLoader_v_IntelliCage_Plus_3):
  DATETIME_FIELDS = (ZipLoader_v_IntelliCage_Plus_3.DATETIME_FIELDS
                     + {"Np": ZipLoader_v_IntelliCage_Plus_3.DATETIME_FIELDS["Np"] + ["LickStartTime"]})
  NOSEPOKE_FIELDS = ['Start', 'End', 'Side',
                     'SideCondition', 'SideError',
                     'TimeError', 'ConditionError',
                     'LickNumber', 'LickContactTime',
                     'LickDuration',
                     'AirState', 'DoorState',
                     'LED1State', 'LED2State',
                     'LED3State',
                     'LickStartTime',
                     ]
  def _extract_session_time_bounds(self, session):
    start, end = super(ZipLoader_v_IntelliCage_Plus_3_1,
                       self)._extract_session_time_bounds(session)
    offset = session.getElementsByTagName('TimeZoneOffset')[0]
    offset = offset.childNodes[0]
    assert offset.nodeType == offset.TEXT_NODE
    offset = offset.nodeValue
    hours, minutes, seconds = map(int, offset.split(':'))
    tz = timezone(timedelta(hours=hours,
                            minutes=minutes,
                            seconds=seconds))
    return start.replace(tzinfo=tz), (end.replace(tzinfo=tz) if end is not None else None)


class ZipLoader_v_version_2_2(_ZipLoaderBase):
  DATETIME_FIELDS = (_ZipLoaderBase.DATETIME_FIELDS
                     + {k: ["Time"] for k in _LOG_ENV_HW})

  VISIT_FIELDS = ['Cage', 'Corner',
                  'AnimalTag', 'Start', 'End', 'ModuleName',
                  'CornerCondition', 'PlaceError',
                  'AntennaNumber', 'AntennaDuration',
                  'PresenceNumber', 'PresenceDuration',
                  'VisitSolution',
                  ]
  VISIT_ID_FIELD = 'VisitID'
  VISIT_TAG_FIELD = 'AnimalTag'

  NOSEPOKE_FIELDS = ['Start', 'End', 'Side',
                     'SideCondition', 'SideError',
                     'TimeError', 'ConditionError',
                     'LicksNumber',
                     'LickContactTime',
                     'LicksDuration',
                     'AirState', 'DoorState',
                     'LED1State', 'LED2State',
                     'LED3State',
                     'LickStartTime',  # Only IC+ v. 3.1
                     ]

  def _getCageCornerSide(self, Cage, Corner, Side):
    if Cage is None:
      return Cage, Corner, Side

    cage = self._cageManager[int(Cage) + 1]
    if Corner is None:
      return cage, Corner, Side

    corner = cage[int(Corner) + 1]
    if Side is None:
      return cage, corner, Side

    return cage, corner, (corner[int(Side) + 1])

  def wrapLog(self, columns):
    return self._columnsToObjects(columns,
                                  ['Time',
                                   'LogCategory',
                                   'LogType',
                                   'Cage',
                                   'Corner',
                                   'Side',
                                   'LogNotes'],
                                  self._makeLog)

  def _makeEnv(self, DateTime, Temperature, Illumination,
               _line):
    return EnvironmentalConditions(DateTime,
                                   float(Temperature),
                                   int(Illumination),
                                   None,
                                   self._source, _line)

  def wrapEnv(self, columns):
     return self._columnsToObjects(columns,
                                  ['Time', 'Temperature',
                                   'Illumination'],
                                  self._makeEnv)

  def wrapHw(self, columns):
    return self._columnsToObjects(columns,
                                  ['Time',
                                   'HardwareType',
                                   'Cage',
                                   'Corner',
                                   'Side',
                                   'State'],
                                  self._makeHw)

  @classmethod
  def extractAndWrapAnimals(cls, columns):
    return cls._columnsToObjects(columns,
                                 ['AnimalName', 'AnimalTag','Sex',
                                  'AnimalNotes'],
                                 cls._makeAnimal)

  @classmethod
  def extractAndWrapGroups(cls, columns):
    return cls.group(columns['AnimalName'],
                     columns['GroupName'])


class ZipLoader_v_version1(_ZipLoaderBase):
  DATETIME_FIELDS = (_ZipLoaderBase.DATETIME_FIELDS
                     + {k: ["DateTime"] for k in _LOG_ENV_HW})

  def _getCageCornerSide(self, Cage, Corner, Side):
    if Cage is None:
      return Cage, Corner, Side

    cage = self._cageManager[int(Cage) + 1]
    if Corner is None:
      return cage, Corner, Side

    corner = cage[int(Corner) + 1]
    if Side is None:
      return cage, corner, Side

    return cage, corner, (corner[int(Side) + 1])

  def _makeEnv(self, DateTime, Temperature, Illumination,
               _line):
    return EnvironmentalConditions(DateTime,
                                   float(Temperature),
                                   int(Illumination),
                                   None,
                                   self._source, _line)

  def wrapEnv(self, columns):
    return self._columnsToObjects(columns,
                                  ['DateTime', 'Temperature', 'Illumination'],
                                  self._makeEnv)

  def wrapLog(self, columns):
    return self._columnsToObjects(columns,
                                  ['DateTime',
                                   'Category',
                                   'Type',
                                   'Cage',
                                   'Corner',
                                   'Side',
                                   'Notes'],
                                  self._makeLog)

  def wrapHw(self, columns):
    return self._columnsToObjects(columns,
                                  ['DateTime',
                                   'Type',
                                   'Cage',
                                   'Corner',
                                   'Side',
                                   'State'],
                                  self._makeHw)

  VISIT_FIELDS = ['Cage', 'Corner',
                  'Animal', 'Start', 'End', 'ModuleName',
                  'CornerCondition', 'PlaceError',
                  'AntennaNumber', 'AntennaDuration',
                  'PresenceNumber', 'PresenceDuration',
                  'VisitSolution',
                  ]
  VISIT_ID_FIELD = 'ID'
  VISIT_TAG_FIELD = 'Animal'

  NOSEPOKE_FIELDS = ['Start', 'End', 'Side',
                     'SideCondition', 'SideError',
                     'TimeError', 'ConditionError',
                     'LicksNumber', 'LickContactTime',
                     'LicksDuration',
                     'AirState', 'DoorState',
                     'LED1State', 'LED2State',
                     'LED3State',
                     'LickStartTime',  # Only IC+ v. 3.1
                     ]

  @classmethod
  def extractAndWrapAnimals(cls, columns):
    return cls._columnsToObjects(columns,
                                 ['Name', 'Tag','Sex', 'Notes'],
                                 cls._makeAnimal)

  @classmethod
  def extractAndWrapGroups(cls, columns):
    return cls.group(columns['Name'],
                     columns['Group'])

ZIP_LOADERS = {
  'version1': ZipLoader_v_version1,
  'version_2_2': ZipLoader_v_version_2_2,
  'intellicage_plus_3': ZipLoader_v_IntelliCage_Plus_3,
  'intellicage_plus_3_1': ZipLoader_v_IntelliCage_Plus_3_1,
}
