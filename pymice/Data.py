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

import sys
if sys.version_info >= (3, 0):
  basestring = str
  unicode = str

import os
import zipfile
import csv
try:
  import cStringIO as io

except ImportError:
  import io

import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.path import Path

from operator import methodcaller, attrgetter
from collections import Container

from .ICNodes import Group # XXX: unnecessary dependency

from ._Tools import timeString, toTimestampUTC, warn
from ._ObjectBase import ObjectBase

class IdentityManager(object):
  def __getitem__(self, x):
    return x

#  def _del_(self):
#    pass


class IntIdentityManager(int):
  def __new__(cls, *args, **kwargs):
    if len(args) + len(kwargs) == 0:
      args = [0]

    return int.__new__(cls, *args, **kwargs)

  def __getitem__(self, x):
    return self.__class__(x)

  def _del_(self):
    pass


#class DictManager(dict):
#  def _del_(self):
#    pass


class Data(object):
  """
  A base class for objects containing behavioural data.
  """

  def __init__(self, getNp=True, getLog=False,
               getEnv=False, getHw=False,
               SourceManager=IdentityManager,
               CageManager=IntIdentityManager,
               AnimalManager=dict):
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
    self.__animalsByName = AnimalManager()

    self.__visits = ObjectBase({
      'Start': toTimestampUTC,
      'End': toTimestampUTC})
    self.__nosepokes = [] #reserved for future use
    self.__log = ObjectBase({'DateTime': toTimestampUTC})
    self.__environment = ObjectBase({'DateTime': toTimestampUTC})
    self.__hardware = ObjectBase({'DateTime': toTimestampUTC})
    self._initCache()

    self._cageManager = CageManager()
    self._sourceManager = SourceManager()

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
    for cache in [self.__visits,
                  self.__log,
                  self.__environment,
                  self.__hardware]:
      for node in cache.get():
        if node:
          node._del_()

    self._cageManager._del_()
    #self._sourceManager._del_()
    #self.__animalsByName._del_()


# caching data
  def _initCache(self):
    self.icSessionStart = None
    self.icSessionEnd = None
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
                    % (mouse, ', '.join(map(str, cages))), stacklevel=2)
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


#  def removeVisits(self, condition="False"):

# data management

  def insertLog(self, log):
    newLog = self.__cloneObjectsWithSourceCageManagers(log)
    self._insertNewLog(newLog)

  def __cloneObjectsWithSourceCageManagers(self, objects):
    return map(methodcaller('clone', self._sourceManager,
                            self._cageManager),
               objects)

  def _insertNewLog(self, lNodes):
    self.__log.put(lNodes)

  def insertEnv(self, env):
    newEnv = self.__cloneObjectsWithSourceCageManagers(env)
    self._insertNewEnv(newEnv)

  def _insertNewEnv(self, eNodes):
    self.__environment.put(eNodes)

  def insertHw(self, hardwareEvents):
    newHw = self.__cloneObjectsWithSourceCageManagers(hardwareEvents)
    self._insertNewHw(newHw)

  def _insertNewHw(self, hNodes):
    self.__hardware.put(hNodes)

  def insertVisits(self, visits):
    newVisits = map(methodcaller('clone', self._sourceManager,
                                 self._cageManager,
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
      print("WARNING: Overwriting group %s." % group)
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

    >>> mice = [ml_l1.getAnimal(m) for m in ['Mickey', 'Minnie']]
    >>> [v.Corner for v in ml_l1.getVisits(mice=mice, order='Start')]
    [4, 1]



    >>> for v in ml_icp3.getVisits(order='Start'):
    ...   print(v.Start.strftime("%Y-%m-%d %H:%M:%S.%f %z"))
    2012-12-18 12:13:14.139000 +0100
    2012-12-18 12:18:55.421000 +0100
    2012-12-18 12:19:55.421000 +0100

    >>> for v in ml_l1.getVisits(mice='Minnie'):
    ...   print(v.Start.strftime("%Y-%m-%d %H:%M:%S.%f %z"))
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
      if isinstance(mice, basestring) or not isinstance(mice, Container):
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
    ...   print(entry.Notes)
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
    ...   print("%.1f" % env.Temperature)
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
    buf = io.StringIO()
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

