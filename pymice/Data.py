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

# original: 60.8%; 1:30 
# refactored ICN: 17.4%; 1:14  
# refactored ICN+Nodes: 17.3%; 1:12 

import os
import zipfile
import csv
import cStringIO
import copy

import dateutil.parser
import pytz

import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.path import Path
import matplotlib.ticker
import numpy as np
from xml.dom import minidom

from operator import methodcaller, attrgetter
from itertools import izip, repeat
from datetime import datetime, timedelta, MINYEAR 
from ICNodes import Animal, Group, Visit, Nosepoke, \
                    LogEntry, EnvironmentalConditions, \
                    AirHardwareEvent, DoorHardwareEvent, LedHardwareEvent,\
                    UnknownHardwareEvent, Session

from _Tools import timeString, ensureFloat, ensureInt, \
                   convertTime, timeToList, \
                   PathZipFile, toTimestampUTC, warn, groupBy
from _FixTimezones import inferTimezones, LatticeOrderer

from _ObjectBase import ObjectBase

callCopy = methodcaller('copy')

class Data(object):
  """
  A base class for objects containing behavioural data.
  """

  def __init__(self, getNp=True, getLog=False,
               getEnv=False, getHw=False):
    """
    @param getNp: whether to load nosepoke data.

    @param getLog: whether to load log.

    @param getEnv: whether to load environmental data.

    @param getHw: whether to load hardware data.
    """
    self.__name2group = {}

    self._getNp = getNp
    self._getLog = getLog
    self._getEnv = getEnv
    self._getHw = getHw

    # change to
    self.__animalsByName = {}

    self.__visits = ObjectBase({
      'Start': toTimestampUTC,
      'End': toTimestampUTC})
    self.__nosepokes = [] #reserved for future use
    self.__log = ObjectBase({'DateTime': toTimestampUTC})
    self.__environment = ObjectBase({'DateTime': toTimestampUTC})
    self.__hardware = ObjectBase({'DateTime': toTimestampUTC})
    self._initCache()

  @property
  def _get_npokes(self):
    warn.deprecated("Obsolete attribute _get_npokes accessed.")
    return self._getNp

  @property
  def _getNpokes(self):
    warn.deprecated("Obsolete attribute _getNpokes accessed.")
    return self._getNp

  @property
  def _getLogs(self):
    warn.deprecated("Obsolete attribute _getLogs accessed.")
    return self._getLog

  def __del__(self):
    for vNode in self.__visits.get():
      if vNode:
        vNode._del_()

# caching data
  def _initCache(self):
    self.icSessionStart = None
    self.icSessionEnd = None
    self.__sessions = np.array([], dtype=object)
    self.__sessionsStarts = np.array([])
    self.__cages = {}
    self.__animal2cage = {}

  def _buildCache(self):
    self.__cages = {}
    self.__animal2cage = {}
    currentCage = None
    animals = []
    cursor = sorted(set((int(c), unicode(a)) for (c, a) in self.__visits.getAttributes('Cage', 'Animal.Name')))

    for cage, animal in cursor:
      if animal not in self.__animal2cage:
        self.__animal2cage[animal] = [cage]

      else:
        self.__animal2cage[animal].append(cage)
        warn.warn("Animal %s found in multiple cages (%s)." %\
                  (animal, ', '.join(map(str, self.__animal2cage[animal]))))
                  #, stacklevel=4)

      # unsure if should be object instead of unicode
      animal = self.__animalsByName[animal]
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

  def getCage(self, mouse):
    """
    >>> ml_icp3.getCage('Minnie')
    1

    >>> ml_icp3.getCage(ml_icp3.getAnimal('Minnie'))
    1

    @return: cage(s) mouse presence has been detected
    @rtype: convertable to int or (convertable to int, ...)
    """
    try:
      cages = self.__animal2cage[unicode(mouse)]

    except KeyError:
      warn.warn("Mouse %s not found in any cage." % mouse, stacklevel=2)
      return None

    if len(cages) != 1:
      warn.warn("Mouse %s found in multiple cages: %s."\
                    % (mouse, ', '.join(map(str,cages))), stacklevel=2)
      return tuple(cages)

    return cages[0]

  def getMice(self):
    """
    @return: names of registered animals
    @rtype: frozenset(unicode, ...)
    """
    return frozenset(self.__animalsByName)

  def getInmates(self, cage=None):
    """
    @param cage: number of the cage
    @type cage: convertable to int

    @return: cages available in data if cage is C{None} animals detected in the cage otherwise
    @rtype: frozenset(int, ...) if cage is C{None} C{frozenset(L{Animal}, ...)} otherwise
    """
    if cage == None:
      return frozenset(self.__cages)

    return self.__cages[int(cage)] # is a frozenset already

  def getStart(self):
    """
    @return: time of the earliest visit registration
    @rtype: datetime
    """
    if self.icSessionStart is not None:
      return self.icSessionStart

    times = self.__visits.getAttributes('Start')
    try:
      return min(times)

    except ValueError:
      return None

  def getEnd(self):
    """
    @return: time of the latest visit registration
    @rtype: datetime
    """
    if self.icSessionEnd is not None:
      return self.icSessionEnd

    times = self.__visits.getAttributes('End')
    try:
      return max(times)

    except ValueError:
      return None


# log analysis
  def _logAnalysis(self, loganalyzers):
    self.excluded = []
    self.loganalyzers = loganalyzers
    for loganalyzer in loganalyzers:
      self.excluded.extend(loganalyzer(self))

  def getExcludedData(self):
    warn.deprecated("Deprecated method getExcludedData() called; use getExcluded() instead.")
    return self.getExcluded()

  def getExcluded(self):
    return list(self.excluded)


#  def removeVisits(self, condition="False"):

# data management

  @staticmethod
  def _newNodes(nodes, cls=None):
    return map(cls.fromDict, nodes)

  def insertLog(self, log):
    newLog = map(methodcaller('clone', IdentityManager(),
                              IntCageManager()),
                 log)
    self._insertNewLog(newLog)

  def _insertNewLog(self, lNodes):
    self.__log.put(lNodes)

  def insertEnv(self, env):
    newEnv = map(methodcaller('clone', IdentityManager(),
                              IntCageManager()),
                 env)
    self._insertNewEnv(newEnv)

  def _insertNewEnv(self, eNodes):
    self.__environment.put(eNodes)

  def insertHw(self, hardwareEvents):
    newHw = map(methodcaller('clone', IdentityManager(),
                              IntCageManager()),
                hardwareEvents)
    self._insertNewHw(newHw)

  def _insertNewHw(self, hNodes):
    self.__hardware.put(hNodes)

  def insertVisits(self, visits):
    newVisits = map(methodcaller('clone', IdentityManager(),
                                 IntCageManager(),
                                 self.__animalsByName),
                    visits)
    self._insertNewVisits(newVisits)

  def _insertNewVisits(self, visits):
    self.__visits.put(visits)

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

    group = Group(Name=Name, Animals=Animals, **kwargs)
    self.__name2group[Name] = group
    return group

  def _unregisterGroup(self, name):
    del self.__name2group[name]

  def _addMember(self, name, animal):
    group = self.__name2group[name]
    animal = self.getAnimal(animal) # XXX sanity
    group.addMember(animal)

  def getAnimal(self, name=None):
    """
    @param name: name of the animal
    @type name: basestring

    @return: animal data if name or aid given else names of animals
    @rtype: Animal if name or aid given else frozenset([unicode, ...])
    """
    if name is not None:
      return self.__animalsByName[unicode(name)]

    return frozenset(self.__animalsByName)

  def _registerAnimal(self, aNode):
    try:
      animal = self.__animalsByName[aNode.Name]

    except KeyError:
      animal = aNode.clone()
      self.__animalsByName[animal.Name] = animal

    else:
      animal.merge(aNode)

    return animal

  # TODO or not TODO
#  def _unregisterAnimal(self, Name = None, aid = None):

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

  def plotMiceCage(self):
    visits = {}
    for v in self.getVisits():
      try:
        visits[unicode(v.Animal)].append((v.Start, int(v.Cage)))

      except KeyError:
        visits[unicode(v.Animal)] = [(v.Start, int(v.Cage))]

    for mouse, data in visits.items():
      cages = []
      times = []
      data.sort()
      lastC, lastT = None, None
      many = False
      for t, c in data:
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

  def plotChannel(self, top=1., bottom=0., startM=None, endM=None):
    #TODO!!!!
    h = top - bottom
    data = self.getVisits()
    startD = min(map(attrgetter('Start'), data))
    endD = max(map(attrgetter('End'), data))
    startR = self.icSessionStart
    endR = self.icSessionEnd

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

  def __filterUnicode(self, data, field, select=None):
    if select is None:
      return data

    key = attrgetter(field)
    if isinstance(select, basestring):
      select = unicode(select)
      return (x for x in data if unicode(key(x)) == select)

    select = frozenset(map(unicode, select))
    return (x for x in data if unicode(key(x)) in select)

  def __filterInt(self, data, field, select=None):
    if select is None:
      return data

    key = attrgetter(field)
    if not isinstance(select, (tuple, list, set, frozenset)):
      select = int(select)
      return (x for x in data if int(key(x)) == select)

    select = frozenset(map(int, select))
    return (x for x in data if int(key(x)) in select)

  @staticmethod
  def __orderBy(data, order):
    if order is None:
      return list(data)

    key = attrgetter(order) if isinstance(order, basestring) else attrgetter(*order)
    return sorted(data, key=key)

  @staticmethod
  def __makeTimeFilter(start, end):
    if start is not None:
      startTimestamp = toTimestampUTC(start)
      if end is not None:
        endTimestamp = toTimestampUTC(end)
        return lambda X: (startTimestamp <= X) * (X < endTimestamp)

      return lambda X: startTimestamp <= X

    if end is not None:
      endTimestamp = toTimestampUTC(end)
      return lambda X: X < endTimestamp

  @staticmethod
  def __makeTimeSelectors(attributeName, start, end):
    if start is None and end is None:
      return {}

    return {attributeName: Data.__makeTimeFilter(start, end)}

  def getVisits(self, mice=None, start=None, end=None, order=None, startTime=None, endTime=None):
    """
    >>> [v.Corner for v in ml_l1.getVisits(order='Start')]
    [4, 1, 2]
    >>> [v.Corner for v in ml_icp3.getVisits(order='Start')]
    [1, 2, 3]
    >>> [v.Corner for v in ml_l1.getVisits(mice='Mickey')]
    [1]
    >>> [v.Corner for v in ml_icp3.getVisits(mice='Jerry', order='Start')]
    [3]
    >>> [v.Corner for v in ml_l1.getVisits(mice=['Mickey', 'Minnie'], order='Start')]
    [4, 1]
    >>> [v.Corner for v in ml_icp3.getVisits(mice=['Jerry', 'Minnie'], order='Start')]
    [1, 3]

    >>> mice = map(ml_l1.getAnimal, ['Mickey', 'Minnie'])
    >>> [v.Corner for v in ml_l1.getVisits(mice=mice, order='Start')]
    [4, 1]



    >>> for v in ml_icp3.getVisits(order='Start'):
    ...   print v.Start.strftime("%Y-%m-%d %H:%M:%S.%f %z")
    2012-12-18 12:13:14.139000 +0100
    2012-12-18 12:18:55.421000 +0100
    2012-12-18 12:19:55.421000 +0100

    >>> for v in ml_l1.getVisits(mice='Minnie'):
    ...   print v.Start.strftime("%Y-%m-%d %H:%M:%S.%f %z")
    2012-12-18 12:30:02.360000 +0000

    @param mice: mouse (or mice) which visits are requested
    @type mice:

    @param start: a lower bound of the visit Start attribute
    @type start: datetime

    @param end: an upper bound of the visit Start attribute
    @type end: datetime

    @param order: attributes that the returned list is ordered by
    @type order: str or (str, ...)

    @param startTime: deprecated, use C{start} instead

    @param endTime: deprecated, use C{end} instead

    @return: visits.
    @rtype: [Visit]
    """
    if startTime is not None:
      warn.deprecated("Obsolete argument 'startTime' used; use 'start' instead")
      if start is not None:
        raise ValueError("Arguments 'start' and 'startTime' are mutually exclusive.")

      start = startTime

    if endTime is not None:
      warn.deprecated("Obsolete argument 'endTime' used; use 'end' instead")
      if end is not None:
        raise ValueError("Arguments 'end' and 'endTime' are mutually exclusive.")

      end = endTime

    selectors = self.__makeTimeSelectors('Start', start, end)
    if mice is not None:
      if isinstance(mice, (basestring, Animal)):
        mice = [mice]

      selectors['Animal.Name'] = map(unicode, mice)

    visits = self.__visits.get(selectors)
    return self.__orderBy(visits, order)

  def getLogs(self, *args, **kwargs):
    """
    @deprecated: use L{getLog} instead.
    """
    warn.deprecated("Obsolete method getLogs accessed.")
    return self.getLog(*args, **kwargs)

  def getLog(self, start=None, end=None, order=None, startTime=None, endTime=None):
    """
    >>> log = ml_icp3.getLog(order='DateTime')
    >>> for entry in log:
    ...   print entry.Notes
    Session is started
    Session is stopped

    @param start: a lower bound of the log entries DateTime attribute
    @type start: datetime

    @param end: an upper bound of the log entries DateTime attribute
    @type end: datetime

    @param order: attributes that the returned list is ordered by
    @type order: str or (str, ...)

    @param startTime: deprecated, use C{start} instead

    @param endTime: deprecated, use C{end} instead

    @return: log entries.
    @rtype: [LogEntry, ...]
    """
    if startTime is not None:
      warn.deprecated("Obsolete argument 'startTime' used; use 'start' instead")
      if start is not None:
        raise ValueError("Arguments 'start' and 'startTime' are mutually exclusive.")

      start = startTime

    if endTime is not None:
      warn.deprecated("Obsolete argument 'endTime' used; use 'end' instead")
      if end is not None:
        raise ValueError("Arguments 'end' and 'endTime' are mutually exclusive.")

      end = endTime

    selectors = self.__makeTimeSelectors('DateTime', start, end)
    log = self.__log.get(selectors)
    return self.__orderBy(log, order)

  def getEnvironment(self, start=None, end=None, order=None, startTime=None, endTime=None):
    """
    >>> for env in ml_icp3.getEnvironment(order=('DateTime', 'Cage')):
    ...   print "%.1f" %env.Temperature
    22.0
    23.6
    22.0
    23.6
    22.0
    23.6
    22.0
    23.6
    22.0
    23.6
    22.0
    23.6
    22.0
    23.6
    22.0
    23.6

    @param start: a lower bound of the sample DateTime attribute
    @type start: datetime

    @param end: an upper bound of the sample DateTime attribute
    @type end: datetime

    @param order: attributes that the returned list is ordered by
    @type order: str or (str, ...)

    @param startTime: deprecated, use C{start} instead

    @param endTime: deprecated, use C{end} instead

    @return: sampled environment conditions.
    @rtype: [EnvironmentalConditions, ...]
    """
    if startTime is not None:
      warn.deprecated("Obsolete argument 'startTime' used; use 'start' instead")
      if start is not None:
        raise ValueError("Arguments 'start' and 'startTime' are mutually exclusive.")

      start = startTime

    if endTime is not None:
      warn.deprecated("Obsolete argument 'endTime' used; use 'end' instead")
      if end is not None:
        raise ValueError("Arguments 'end' and 'endTime' are mutually exclusive.")

      end = endTime

    selectors = self.__makeTimeSelectors('DateTime', start, end)
    env = self.__environment.get(selectors)
    return self.__orderBy(env, order)

  def getHardwareEvents(self, start=None, end=None, order=None, startTime=None, endTime=None):
    """
    @param start: a lower bound of the event DateTime attribute
    @type start: datetime

    @param endTime: an upper bound of the event DateTime attribute
    @type endTime: datetime

    @param order: attributes that the returned list is ordered by
    @type order: str or (str, ...)

    @param startTime: deprecated, use C{start} instead

    @param endTime: deprecated, use C{end} instead

    @return: hardware events.
    @rtype: [HardwareEvent, ...]
    """
    if startTime is not None:
      warn.deprecated("Obsolete argument 'startTime' used; use 'start' instead")
      if start is not None:
        raise ValueError("Arguments 'start' and 'startTime' are mutually exclusive.")

      start = startTime

    if endTime is not None:
      warn.deprecated("Obsolete argument 'endTime' used; use 'end' instead")
      if end is not None:
        raise ValueError("Arguments 'end' and 'endTime' are mutually exclusive.")

      end = endTime

    selectors = self.__makeTimeSelectors('DateTime', start, end)
    hw = self.__hardware.get(selectors)
    return self.__orderBy(hw, order)

  def save(self, filename, force=False):
    """
    An experimental method for saving the data.

    @param filename: path to the file data has to be saved to; if filename does
                     not end with '.zip', the suffix is being appended.
    @type filename: basestring

    @param force: whether to overwrite an existing file
    @type force: bool
    """
    if not filename.lower().endswith('.zip'):
      filename += '.zip'

    if os.path.exists(filename) and not force:
      raise ValueError("File %s already exists." % filename)

    fh = zipfile.ZipFile(filename, 'w')

    # Animals
    buf = cStringIO.StringIO()
    keys = set()
    animals = {}
    for animal in self.__animals: # FIXME: __animals nor _aid is no longer valid
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

    for visit in self.__visits.get():
      visKeys.update(visit.keys())
      sources.add(visit._source)
      visits[id(visit)] = str(len(visits)) #vid

    for nosepoke in self.__nosepokes:
      npKeys.update(nosepoke.keys())
      sources.add(nosepoke._source)

    for log in self.__log.get():
      logKeys.update(log.keys())
      sources.add(log._source)

    for env in self.__environment.get():
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
      for visit in self.__visits.get():
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
      for log in self.__log.get():
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
      for env in self.__environment.get():
        _sid = sources[env._source]
        DateTime = timeString(env.DateTime)
        row = env.select(logKeys)
        row = [DateTime] + row + [_sid]
        writer.writerow(row)

      fh.writestr('IntelliCage/Environment.txt', buf.getvalue(), zipfile.ZIP_DEFLATED)
      buf.reset()
      buf.truncate()

    fh.close()



try:
  from pymice._C import emptyStringToNone

except Exception as e:
  print type(e), e

  def emptyStringToNone(l):
    for i, x in enumerate(l):
      if type(x) is list:
        emptyStringToNone(x)

      elif x == '':
        l[i] = None

    return l


convertFloat = methodcaller('replace', ',', '.')


def fixSessions(sortedTimepoints, sessions=[]):
  assert len(sessions) == 1
  session = sessions[0]
  sortedTimezones = inferTimezones(sortedTimepoints, session.Start, session.End)
  for timepoint, timezone in zip(sortedTimepoints, sortedTimezones):
    timepoint.append(timezone)


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
                     'Category': 'LogCategory',
                     'Notes': 'LogNotes',
                    },
             'HardwareEvents': {'Type': 'HardwareType',
                               },
            }

  _aliasesZip = {'Animals': {'AnimalName': 'Name',
                             'AnimalTag': 'Tag',
                             'GroupName': 'Group',
                             'AnimalNotes': 'Notes',
                            },
                 'IntelliCage/Visits': {#'AnimalTag': 'AnimalTag',
                                        'Animal': 'AnimalTag',
                                        'ID': 'VisitID',
                                        #'VisitID': '_vid',
                                        #'ModuleName': 'Module',
                                       },
                 'IntelliCage/Nosepokes': {'LicksNumber': 'LickNumber',
                                           'LicksDuration': 'LickDuration',
                                           #'VisitID': '_vid',
                                          },
                 'IntelliCage/Log': {#'LogType': 'Type',
                                     #'Log': 'Type',
                                     #'LogCategory': 'Category',
                                     #'LogNotes': 'Notes',
                                    },
                 'IntelliCage/HardwareEvents': {'HardwareType': 'Type',
                                               },
                }
  _convertZip = {'Animals': {#'Tag': int,
                            },
                 'IntelliCage/Visits': {#'Tag': int,
                                        #'_vid': int,
                                        'Start': timeToList,
                                        'End': timeToList,
                                        'CornerCondition': convertFloat,
                                        'PlaceError': convertFloat,
                                        'AntennaDuration': convertFloat,
                                        'PresenceDuration': convertFloat,
                                       },
                 'IntelliCage/Nosepokes': {#'_vid': int,
                                           'Start': timeToList,
                                           'End': timeToList,
                                           'LickContactTime': convertFloat,
                                           'LickDuration': convertFloat,
                                           'SideCondition': convertFloat,
                                           'SideError': convertFloat,
                                           'TimeError': convertFloat,
                                           'ConditionError': convertFloat,
                                          },
                 'IntelliCage/Log': {'DateTime': timeToList,
                                    },
                 'IntelliCage/Environment': {'DateTime': timeToList,
                                             'Temperature': convertFloat,
                                            },
                 'IntelliCage/HardwareEvents': {'DateTime': timeToList,
                                               },
                }

  def __init__(self, fname, getNp=True, getLog=False, getEnv=False, getHw=False,
               logAnalyzers=(), tzinfo=pytz.UTC, **kwargs):
    """
    @param fname: a path to the data file.
    @type fname: basestring

    @param getNp: whether to load nosepoke data.
    @type getNp: bool

    @param getLog: whether to load log.
    @type getLog: bool

    @param getEnv: whether to load environmental data.
    @type getEnv: bool

    @param getHw: whether to load hardware data.
    @type getHw: bool

    @param logAnalyzers: a collection of log analysers (to be implemented)
    """
    for key, value in kwargs.items():
      if key in ('get_npokes', 'getNpokes', 'getNosepokes'):
        warn.deprecated("Obsolete argument %s given for Loader constructor." % key)
        getNp = value

      elif key == 'getLogs':
        warn.deprecated("Obsolete argument %s given for Loader constructor." % key)
        getLog = value

      elif key == 'getEnvironment':
        warn.deprecated("Obsolete argument %s given for Loader constructor." % key)
        getEnv = value

      elif key in ('getHardware', 'getHardwareEvents'):
        warn.deprecated("Obsolete argument %s given for Loader constructor." % key)
        getHw = value

      elif key == 'loganalyzers':
        logAnalyzers = value

      else:
        warn.warn("Unknown argument %s given for Loader constructor." % key, stacklevel=2)

    if len(logAnalyzers) > 0:
      getLog = True

    Data.__init__(self, getNp=getNp, getLog=getLog, getEnv=getEnv, getHw=getHw)

    self._fnames = (fname,)

    self.appendData(fname)

    for log in self.getLog():
      if log.Category != 'Info' or log.Type != 'Application':
        continue

      if log.Notes == 'Session is started':
        self.icSessionStart = log.DateTime

      elif log.Notes == 'Session is stopped':
        self.icSessionEnd = log.DateTime

      else:
        print 'unknown Info/Application message: %s' % msg

    self._logAnalysis(logAnalyzers)


  def _loadZip(self, zf, getHw=False, source=None):
    tagToAnimal = AnimalManager(self._loadAnimals(zf))

    try:
      fh = zf.open('Sessions.xml')
      dom = minidom.parse(fh)
      aos = dom.getElementsByTagName('ArrayOfSession')[0]
      ss = aos.getElementsByTagName('Session')
      sessions = []
      for session in ss:
        offset = session.getElementsByTagName('TimeZoneOffset')[0]
        offset = offset.childNodes[0]
        assert offset.nodeType == offset.TEXT_NODE
        offset = offset.nodeValue

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

        if end is not None and start.tzinfo != end.tzinfo:
          warn.warn(UserWarning('Timezone changed!'))

        for sessionStart, sessionEnd in sessions:
          if sessionEnd is None:
            continue

          if sessionStart < start < sessionEnd or\
             end is not None and sessionStart < end < sessionEnd or\
             (end is not None and start <= sessionStart and sessionEnd <= end) or\
             (end is not None and sessionStart <= start and end <= sessionEnd):
              warn.warn(UserWarning('Temporal overlap of sessions!'))

        sessions.append(Session(Start=start, End=end))

      sessions = sorted(sessions, key=attrgetter('Start'))

    except:
      sessions = None
      pass

    timeOrderer = LatticeOrderer()

    visits = self._fromZipCSV(zf, 'IntelliCage/Visits', source=source)
    vids = visits['VisitID']

    if sessions is not None:
      # for es, ee, ss, ll in izip(visits['Start'], visits['End'], visits['_source'], visits['_line']):
      #   ee._type = 'v.End'
      #   ee._source = ss
      #   ee._line = ll
      #   es._type = 'v.Start'
      #   es._source = ss
      #   es._line = ll
      vEnds = visits['End']
      vStarts = visits['Start']

      timeOrderer.coupleTuples(vStarts, vEnds)
      timeOrderer.makeOrderedSequence(vEnds)
      timeOrderer.addOrderedSequence(np.array(vStarts + [None], dtype=object)[np.argsort(map(int, vids))])

    else: #XXX
      timeToFix = visits['End'] + visits['Start'] 

    nosepokes = None
    if self._getNp:
      vid2tag = dict(zip(vids, visits['AnimalTag']))

      nosepokes = self._fromZipCSV(zf, 'IntelliCage/Nosepokes', source=source)

      npVids = nosepokes['VisitID']

      if sessions is not None:
        # for es, ee, ss, ll in izip(nosepokes['Start'], nosepokes['End'], nosepokes['_source'], nosepokes['_line']):
        #   ee._type = 'n.End'
        #   ee._source = ss
        #   ee._line = ll
        #   es._type = 'n.Start'
        #   es._source = ss
        #   es._line = ll

        npEnds = nosepokes['End']
        npStarts = nosepokes['Start']
        timeOrderer.coupleTuples(npStarts, npEnds)
        timeOrderer.makeOrderedSequence(npEnds)

        npStarts = np.array(npStarts + [None], dtype=object)
        npTags = np.array(map(vid2tag.__getitem__, npVids))
        npSides = np.array(map(int, nosepokes['Side'])) % 2 # no bilocation assumed
        # XXX                   ^ - ugly... possibly duplicated

        for tag in tagToAnimal:
          for side in (0, 1): # tailpokes correction
            timeOrderer.addOrderedSequence(npStarts[(npTags == tag) * (npSides == side)])

      else: #XXX
        timeToFix.extend(nosepokes['End'])
        timeToFix.extend(nosepokes['Start'])

      for vid in npVids:
        if vid not in vid2tag:
          warn.warn('Unmatched nosepokes: %s' % vid)

    result = {}

    if self._getLog:
      log = self._fromZipCSV(zf, 'IntelliCage/Log', source=source)
      if sessions is not None:
        timeOrderer.addOrderedSequence(log['DateTime'])

      else: #XXX
        timeToFix.extend(log['DateTime'])

    if self._getEnv:
      environment = self._fromZipCSV(zf, 'IntelliCage/Environment', source=source)
      if environment is not None:
        if sessions is not None:
          # for ee, ss, ll in izip(environment['DateTime'], environment['_source'], environment['_line']):
          #   ee._type = 'e.DateTime'
          #   ee._source = ss
          #   ee._line = ll
          timeOrderer.addOrderedSequence(environment['DateTime'])

        else:
          timeToFix.extend(environment['DateTime'])

    if self._getHw:
      hardware = self._fromZipCSV(zf, 'IntelliCage/HardwareEvents', source=source)
      if hardware is not None:
        if sessions is not None:
          timeOrderer.addOrderedSequence(hardware['DateTime'])

        else: #XXX
          timeToFix.extend(hardware['DateTime'])

        #hardware = self._makeDicts(hardware)

      #else:
      #  hardware = []

      #result['hardware'] = hardware

    #XXX important only when timezone changes!
    if sessions is not None:
      fixSessions(timeOrderer.pullOrdered(), sessions)

    else:
      map(methodcaller('append', pytz.utc), timeToFix) # UTC assumed

    visits['Start'] = [datetime(*t) for t in visits['Start']]
    visits['End'] = [datetime(*t) for t in visits['End']]
    if self._getNp:
      nosepokes['Start'] = [datetime(*t) for t in nosepokes['Start']]
      nosepokes['End'] = [datetime(*t) for t in  nosepokes['End']]

    visitLoader = ZipLoader(source, IntCageManager(), tagToAnimal)
    vNodes = visitLoader.loadVisits(visits, nosepokes)
    self._insertNewVisits(vNodes)

    if self._getLog:
      log['DateTime'] = [datetime(*x) for x in log['DateTime']]
      lNodes = visitLoader.loadLog(log)
      self._insertNewLog(lNodes)

    if self._getEnv:
      environment['DateTime'] = [datetime(*x) for x in environment['DateTime']]
      eNodes = visitLoader.loadEnv(environment)
      self._insertNewEnv(eNodes)

    if self._getHw:
      hardware['DateTime'] = [datetime(*x) for x in hardware['DateTime']]
      hNodes = visitLoader.loadHw(hardware)
      self._insertNewHw(hNodes)

    return result

  def _fromZipCSV(self, zf, path, source=None, oldLabels=None):
    try:
      fh = zf.open(path + '.txt')

    except KeyError:
      return

    return self._fromCSV(fh, source=source,
                         aliases=self._aliasesZip.get(path),
                         convert=self._convertZip.get(path),
                         oldLabels=oldLabels)

  @staticmethod
  def _fromCSV(fname, source=None, aliases=None, convert=None, oldLabels=None):
    if isinstance(fname, basestring):
      fname = open(fname, 'rb')

    reader = csv.reader(fname, delimiter='\t')
    data = list(reader)
    fname.close()

    return Loader.__fromCSV(data, source, aliases, convert, oldLabels)

  @staticmethod
  def __fromCSV(data, source, aliases, convert, oldLabels):
    if len(data) == 0:
      return

    labels = data.pop(0)
    if isinstance(oldLabels, set):
      oldLabels.clear()
      oldLabels.update(labels)

    if aliases is not None:
      labels = [aliases.get(l, l) for l in labels]

    n = len(data)
    if n == 0:
      return dict((l, []) for l in labels)

    emptyStringToNone(data)
    data = dict(zip(labels, zip(*data)))
    if source is not None:
      assert '_source' not in data
      data['_source'] = [source] * n

      assert '_line' not in data
      data['_line'] = range(1, n + 1)

    if convert is not None:
      for label, f in convert.items():
        if label in data:
          data[label] = map(f, data[label])

    return data


  def __repr__ (self):
    """
    Nice string representation for prtinting this class.
    """
    mystring = 'IntelliCage data loaded from: %s' %\
               self._fnames.__str__()
    return mystring

  def _loadAnimals(self, zf):
    animalsLabels = set()
    animals = self._fromZipCSV(zf, 'Animals', oldLabels=animalsLabels)

    animalGroup = animals.pop('Group')
    #animals = self._makeDicts(animals )
    tags = animals['Tag']
    animals = map(Animal.fromRow,
                  animals['Name'],
                  tags,
                  animals.get('Sex', ()),
                  animals.get('Notes', ()))

    animalNames = set()
    groups = {}
    tag2Animal = {}
    for group, animal, tag in zip(animalGroup, animals, tags):
      assert tag not in tag2Animal
      name = animal.Name
      assert name not in animalNames
      tag2Animal[tag] = name
      animalNames.add(name)

      if group is not None:
        try:
          groups[group]['Animals'].append(name)

        except KeyError:
          groups[group] = {'Animals': [name],
                           'Name': group}

    for animal in animals:
      self._registerAnimal(animal)

    for group in groups.values():
      self._registerGroup(**group)

    return dict((t, self.getAnimal(n)) for t, n in tag2Animal.items())

  def appendData(self, fname):
    """
    Process one input file and append data to self.data
    """
    fname = fname.encode('utf-8')
    print 'loading data from %s' % fname
    #sid = self._registerSource(fname.decode('utf-8'))

    if fname.endswith('.zip') or os.path.isdir(fname):
      if isinstance(fname, basestring) and os.path.isdir(fname):
        zf = PathZipFile(fname)

      else:
        zf = zipfile.ZipFile(fname)

      data = self._loadZip(zf,
                           getHw=self._getHw,
                           source=fname.decode('utf-8'))

      if self._getHw:
        self._insertHardware(data['hardware'])

    self._buildCache()


  @staticmethod
  def fromCSV(fname, lines = False):
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
      if lines:
        assert 'line' not in result
        result['_line'] = range(1, n + 1)

    except StopIteration:
      pass

    finally:
      fname.close()

    return result


class Merger(Data):
  """
  >>> mm = Merger(ml_icp3, ml_l1)
  >>> for v in mm.getVisits(order='Start'):
  ...   print '%s %d %s' % (str(v.Animal), len(v.Nosepokes), list(v.Animal.Tag)[0])
  Minnie 0 1337
  Mickey 1 42
  Jerry 2 69
  Minnie 1 1337
  Mickey 1 42
  Jerry 2 69

  >>> mm = Merger(ml_empty, ml_l1)
  >>> for v in mm.getVisits(order='Start'):
  ...   print '%s %d' % (str(v.Animal), len(v.Nosepokes))
  Minnie 1
  Mickey 1
  Jerry 2

  >>> mm = Merger(ml_retagged, ml_l1)
  >>> for v in mm.getVisits(order='Start'):
  ...   print '%s %d' % (str(v.Animal), len(v.Nosepokes))
  ...   print "  %s" % (', '.join(sorted(v.Animal.Tag)))
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
  #TODO: common interface, not inheritance
  def __init__(self, *dataSources, **kwargs):
    """
    Usage: Merger(data_1, [data_2, ...] [parameters])

    @type dataSources: [Data, ...]

    @kwparam getNp: whether to load nosepoke data (defaults to False).
    @type getNp: bool

    @kwparam getLog: whether to load log (defaults to False).
    @type getLog: bool

    @kwparam getEnv: whether to load environmental data (defaults to False).
    @type getEnv: bool

    @kwparam getHw: whether to load hardware data (defaults to False).
    @type getHw: bool

    @kwparam ignoreMiceDifferences: whether to ignore encountered differences
                                    in animal description (e.g. sex)
    @type ignoreMiceDifferences: bool
    """
    getNp = kwargs.pop('getNp', True)
    getLog = kwargs.pop('getLog', False)
    getEnv = kwargs.pop('getEnv', False)
    getHw = kwargs.pop('getHw', False)
    logAnalyzers = kwargs.pop('logAnalyzers', [])

    self._ignoreMiceDifferences = kwargs.pop('ignoreMiceDifferences', False)

    for key, value in kwargs.items():
      if key in ('get_npokes', 'getNpokes', 'getNosepokes'):
        warn.deprecated("Obsolete argument %s given for Merger constructor." % key)
        getNp = value

      elif key == 'getLogs':
        warn.deprecated("Obsolete argument %s given for Merger constructor." % key)
        getLog = value

      elif key == 'getEnvironment':
        warn.deprecated("Obsolete argument %s given for Merger constructor." % key)
        getEnv = value

      elif key in ('getHardware', 'getHardwareEvents'):
        warn.deprecated("Obsolete argument %s given for Merger constructor." % key)
        getHw = value

      elif key == 'loganalyzers':
        warn.deprecated("Obsolete argument %s given for Merger constructor." % key)
        logAnalyzers = value

      else:
        warn.warn("Unknown argument %s given for Merger constructor" % key, stacklevel=2)

    if len(logAnalyzers) > 0:
      getLog = True

    Data.__init__(self, getNp=getNp, getLog=getLog, getEnv=getEnv, getHw=getHw)

    self._dataSources = map(str, dataSources)

    self.__topTime = datetime(MINYEAR, 1, 1, tzinfo=pytz.timezone('Etc/GMT-14'))

    for dataSource in self._sortDataSources(dataSources):
      try:
        self.appendDataSource(dataSource)

      except:
        print "ERROR processing %s" % dataSource
        raise

    self._logAnalysis(logAnalyzers)

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

    >>> map(methodcaller('getStart'),
    ...     Merger._sortDataSources([FakeData(), FakeData(dtA),
    ...                              FakeData(dtB), FakeData(dtA)])) == [dtA, dtA, dtB, None]
    True

    >>> map(methodcaller('getStart'),
    ...     Merger._sortDataSources([FakeData(dtA),
    ...                              FakeData(dtB), FakeData(dtA)])) == [dtA, dtA, dtB]
    True

    >>> map(methodcaller('getStart'),
    ...     Merger._sortDataSources([FakeData(), FakeData(), FakeData()])) == [None, None, None]
    True
    """
    sourcesByStartPresence = groupBy(dataSources, getKey=lambda x: x.getStart() is not None)
    return sorted(sourcesByStartPresence.get(True, []), key=methodcaller('getStart')) \
           + sourcesByStartPresence.get(False, [])

  def __repr__(self):
    """
    @return: Nice string representation for prtinting this class.
    """
    mystring = 'IntelliCage data loaded from: %s' %\
                str(self._dataSources)
    return mystring

  def plotData(self):
    # FIXME: obsoleted
    #fig, ax = plt.subplots()
    ax = plt.gca()
    ax.xaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda x, y: hTime(x)))
    plt.xticks(rotation=10)
    labels = []
    yticks = []
    times = []
    for i, dataSource in enumerate(self._dataSources):
      labels.append(str(i))
      start = dataSource.getStart()
      end = dataSource.getEnd()
      #plt.broken_barh([(start, end - start)], [i - 0.4, 0.8])
      times.extend([start, end])
      dataSource.plotChannel(i + 0.6, i + 1.4)
      yticks.append(i)

    plt.yticks(yticks, labels)
    start = min(times)
    end = max(times)
    span = end - start
    plt.xlim(start - 0.1 * span, end + 0.1 * span)
    plt.ylim(0, len(self._dataSources) + 1)

  def plotChannelR(self, top=1., bottom=0.):
    h = top - bottom
    l = len(self._dataSources)
    h2 = h / l
    starts, ends = [], []

    for i, dataSource in enumerate(self._dataSources):
      start, end = dataSource.plotChannelR(bottom + i * h2, bottom + (i + 1) * h2)
      starts.append(start)
      ends.append(end)

    if self.maskTimeStart is not None and self.maskTimeEnd is not None:
      left = self.maskTimeStart if self.maskTimeStart is not None else self.getStart()
      right = self.maskTimeEnd if self.maskTimeEnd is not None else self.getEnd()
      ax = plt.gca()
      codes = [Path.MOVETO, Path.LINETO]
      verts = [(left, top), (right, top)]
      if self.maskTimeEnd is not None:
        codes.append(Path.LINETO)
        ends.append(self.maskTimeEnd)

      else:
        codes.append(Path.MOVETO)

      verts.append((right, bottom))
      codes.append(Path.LINETO)
      verts.append((left, bottom))
      if self.maskTimeStart is not None:
        verts.append((left, top))
        codes.append(Path.CLOSEPOLY)
        starts.append(self.maskTimeStart)

      path = Path(verts, codes)
      patch = patches.PathPatch(path, facecolor='none', edgecolor='red')
      ax.add_patch(patch)
      

    return min(starts), max(ends)

  def appendDataSource(self, dataSource):
    if dataSource.icSessionStart != None:
      if self.icSessionStart != None and self.icSessionEnd != None:
        if self.icSessionStart < dataSource.icSessionStart\
          and self.icSessionEnd > dataSource.icSessionStart:
          print 'Overlap of IC sessions detected'

    if dataSource.icSessionEnd != None:
      if self.icSessionStart != None and self.icSessionEnd != None:
        if self.icSessionStart < dataSource.icSessionEnd\
          and self.icSessionEnd > dataSource.icSessionEnd:
          print 'Overlap of IC sessions detected'

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
          print "Possible temporal overlap of visits"

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
        maxEnd.extend(np.End for v in visits if v.Nosepokes for np in v.Nosepokes)

      self.__topTime = max(maxEnd)

    if self._getHw and hardware:
      self.__topTime = max(self.__topTime, max(hw.DateTime for hw in hardware))

    if self._getEnv and env:
      self.__topTime = max(self.__topTime, max(en.DateTime for en in env))

    if self._getLog and log:
      self.__topTime = max(self.__topTime, max(l.DateTime for l in log))

    self._buildCache()

  @staticmethod
  def _newNodes(nodes, cls=None):
    return map(copy.copy, nodes)


class IntCageManager(int):
  @classmethod
  def get(cls, val):
    return cls(val)

  def getCageCorner(self, cage, corner):
    cg = self.get(cage)
    return cg, cg.get(corner)


class IdentityManager(object):
  @staticmethod
  def get(x):
    return x


class AnimalManager(dict):
  def get(self, key):
    return self[key]


class ZipLoader(object):
  def __init__(self, source, cageManager, animalManager):
    self.__animalManager = animalManager
    self.__cageManager = cageManager
    self.__source = source

  def __makeVisit(self, Cage, Corner, AnimalTag, Start, End, ModuleName,
                CornerCondition, PlaceError,
                AntennaNumber, AntennaDuration, PresenceNumber, PresenceDuration,
                VisitSolution, _line, nosepokeRows):
    animal = self.__animalManager.get(AnimalTag)
    cage, corner = self.__cageManager.getCageCorner(Cage, Corner)

    Nosepokes = None
    if nosepokeRows is not None:
      Nosepokes = tuple(self.__makeNosepoke(corner, row)\
                        for row in sorted(nosepokeRows))

    return Visit(Start, corner, animal, End,
                 unicode(ModuleName) if ModuleName is not None else None,
                 cage,
                 int(CornerCondition) if CornerCondition is not None else None,
                 int(PlaceError) if PlaceError is not None else None,
                 int(AntennaNumber) if AntennaNumber is not None else None,
                 timedelta(seconds=float(AntennaDuration)) if AntennaDuration is not None else None,
                 int(PresenceNumber) if PresenceNumber is not None else None,
                 timedelta(seconds=float(PresenceDuration)) if PresenceDuration is not None else None ,
                 int(VisitSolution) if VisitSolution is not None else None,
                 self.__source, _line,
                 Nosepokes)

  def __makeNosepoke(self, sideManager, (Start, End, Side,
                     SideCondition, SideError, TimeError, ConditionError,
                     LickNumber, LickContactTime, LickDuration,
                     AirState, DoorState, LED1State, LED2State, LED3State,
                     _line)):

    return Nosepoke(Start, End,
                    sideManager.get(Side) if Side is not None else None,
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
                    self.__source, _line)

  def loadVisits(self, visitsCollumns, nosepokesCollumns=None):
    cages = visitsCollumns['Cage']
    corners = visitsCollumns['Corner']

    if nosepokesCollumns is not None:
      vIDs = visitsCollumns['VisitID']
      vNosepokes = self.__assignNosepokesToVisits(nosepokesCollumns, vIDs)

    else:
      vNosepokes = ()

    vColValues = [cages, corners] + [visitsCollumns.get(x, ()) \
                  for x in ['AnimalTag', 'Start', 'End', 'ModuleName',
                            'CornerCondition', 'PlaceError',
                            'AntennaNumber', 'AntennaDuration',
                            'PresenceNumber', 'PresenceDuration',
                            'VisitSolution',]]
    vRows = max(map(len, vColValues))
    vLines = range(1, 1 + vRows)
    vColValues.append(vLines)
    vColValues.append(vNosepokes)
    return map(self.__makeVisit, *vColValues)

  def __assignNosepokesToVisits(self, nosepokesCollumns, vIDs):
    vNosepokes = [[] for _ in vIDs]
    vidToNosepokes = dict((vId, nps) for vId, nps in izip(vIDs, vNosepokes))

    nColValues = [nosepokesCollumns.get(x, repeat(None)) \
                  for x in  ['Start', 'End', 'Side',
                             'SideCondition', 'SideError',
                             'TimeError', 'ConditionError',
                             'LickNumber', 'LickContactTime',
                             'LickDuration',
                             'AirState', 'DoorState',
                             'LED1State', 'LED2State',
                             'LED3State']]
    nIDs = nosepokesCollumns['VisitID']
    nRows = len(nIDs)
    nLines = range(1, 1 + nRows)
    nColValues.append(nLines)

    for vId, row in izip(nIDs, izip(*nColValues)):
      vidToNosepokes[vId].append(row)

    return vNosepokes

  def __makeLog(self, DateTime, Category, Type,
                Cage, Corner, Side, Notes, _line):
    cage, corner, side = None, None, None
    if Cage is not None:
      cage = self.__cageManager.get(Cage)
      if Corner is not None:
        corner = cage.get(Corner)
        if Side is not None:
          side = corner.get(Side)

    return LogEntry(DateTime, unicode(Category), unicode(Type),
                    cage, corner, side,
                    unicode(Notes) if Notes is not None else None,
                    self.__source,
                    _line)

  def loadLog(self, columns):
    colValues = self._getColumnValues(['DateTime',
                                       'LogCategory',
                                       'LogType',
                                       'Cage',
                                       'Corner',
                                       'Side',
                                       'LogNotes'], columns)
    return map(self.__makeLog, *colValues)

  def __makeEnv(self, DateTime, Temperature, Illumination, Cage,
                _line):
    return EnvironmentalConditions(DateTime,
                                   float(Temperature),
                                   int(Illumination),
                                   self.__cageManager.get(Cage),
                                   self.__source, _line)

  def loadEnv(self, columns):
    colValues = self._getColumnValues(['DateTime',
                                       'Temperature',
                                       'Illumination',
                                       'Cage'], columns)
    return map(self.__makeEnv, *colValues)

  __hwClass = {'0': AirHardwareEvent,
               '1': DoorHardwareEvent,
               '2': LedHardwareEvent,
               }

  def __makeHw(self, DateTime, Type, Cage, Corner, Side, State, _line):
    corner, side = Corner, Side
    cage = self.__cageManager.get(Cage)
    if corner is not None:
      corner = cage.get(corner)
      if side is not None:
        side = corner.get(Side)

    try:
      return self.__hwClass[Type](DateTime, cage, corner, side,
                                  int(State), self.__source, _line)

    except KeyError:
      return UnknownHardwareEvent(DateTime, int(Type), cage, corner, side,
                                  int(State), self.__source, _line)

  def loadHw(self, columns):
    colValues = self._getColumnValues(['DateTime',
                                       'Type',
                                       'Cage',
                                       'Corner',
                                       'Side',
                                       'State'], columns)
    return map(self.__makeHw, *colValues)

  def _getColumnValues(self, columnNames, columns):
    colValues = map(columns.get,
                    columnNames)
    n = max(map(len, colValues))
    colValues.append(range(1, n + 1))
    return colValues


if __name__ == '__main__':
  import doctest
  testDir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../test'))
  TEST_GLOBALS = {
    #XXX: ml_l1 - not sure if data format is valid
    'ml_l1': Loader(os.path.join(testDir, 'legacy_data.zip')),
    #'ml_a1': Loader(os.path.join(testDir, 'analyzer_data.txt'), getNpokes=True),
    'ml_icp3': Loader(os.path.join(testDir, 'icp3_data.zip'),
                      getLog=True, getEnv=True),
    'ml_empty': Loader(os.path.join(testDir, 'empty_data.zip')),
    'ml_retagged': Loader(os.path.join(testDir, 'retagged_data.zip')),
    }

  doctest.testmod(extraglobs=TEST_GLOBALS)
