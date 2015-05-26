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
import os
import zipfile
import csv
import cStringIO
import copy

import warnings
import dateutil.parser
import pytz

import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.path import Path
import matplotlib.ticker
import numpy as np
from xml.dom import minidom

from operator import itemgetter, methodcaller, attrgetter
from itertools import izip, repeat
from datetime import datetime, timedelta, MINYEAR 
from ICNodes import DataNode, AnimalNode, GroupNode, VisitNode, NosepokeNode,\
                    LogNode, EnvironmentNode, HardwareEventNode, SessionNode

from _Tools import timeString, deprecated, ensureFloat, ensureInt, \
                   convertTime, timeToList, timeListQueue,\
                   PathZipFile, toTimestampUTC

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
    self.__animals = []
    self.__animalsByName = {}

    self.__visits = []
    self.__nosepokes = [] #reserved for future use
    self.__log = []
    self.__environment = []
    self.__hardware = []

  @property
  def _get_npokes(self):
    deprecated("Obsolete attribute _get_npokes accessed.")
    return self._getNp

  @property
  def _getNpokes(self):
    deprecated("Obsolete attribute _getNpokes accessed.")
    return self._getNp

  @property
  def _getLogs(self):
    deprecated("Obsolete attribute _getLog accessed.")
    return self._getLog

  def __del__(self):
    for vNode in self.__visits:
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
    self.__animalVisits = {}
    self.__visitsStart = None
    self.__logDateTime = None
    self.__envDateTime = None
    self.__hwDateTime = None

  def _buildCache(self):
    # build cache
    self.__cages = {}
    self.__animal2cage = {}
    currentCage = None
    animals = []
    cursor = sorted(set((int(v.Cage), unicode(v.Animal)) for v in self.__visits))

    for cage, animal in cursor:
      if animal not in self.__animal2cage:
        self.__animal2cage[animal] = [cage]

      else:
        self.__animal2cage[animal].append(cage)
        warnings.warn("Animal %s found in multiple cages (%s)." %\
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

    for animal in self.getMice():
      if animal not in self.__animal2cage:
        self.__animal2cage[animal] = []

    animals = map(unicode, map(attrgetter('Animal'), self.__visits))
    self.__animalVisits = dict((m, np.array([a == m for a in animals],
                                   dtype=bool)) for m in self.getMice())
    self.__visitsStart = np.array(map(toTimestampUTC, map(attrgetter('Start'),
                                                 self.__visits)))

    if self._getLog:
      self.__logDateTime = np.array(map(toTimestampUTC, map(attrgetter('DateTime'),
                                                   self.__log)))

    if self._getEnv:
      self.__envDateTime = np.array(map(toTimestampUTC, map(attrgetter('DateTime'),
                                                            self.__environment)))

    if self._getHw:
      self.__hwDateTime = np.array(map(toTimestampUTC, map(attrgetter('DateTime'),
                                                           self.__hardware)))

  def getCage(self, mouse):
    """
    @return: cage(s) mouse presence has been detected
    @rtype: convertable to int or (convertable to int, ...)
    """
    cages = self.__animal2cage[mouse]
    if len(cages) != 1:
      if len(cages) == 0:
        warnings.warn("Mouse %s not found in any cage." % mouse, stacklevel=2)
        return None

      warnings.warn("Mouse %s found in multiple cages: %s."\
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
    @rtype: frozenset(int, ...) if cage is C{None} C{frozenset(L{AnimalNode}, ...)} otherwise
    """
    if cage == None:
      return frozenset(self.__cages)

    return self.__cages[int(cage)] # is a frozenset already

#  def getFirstLick(self, corners = (), mice=()):

  def getStart(self):
    """
    @return: timestamp of the earliest visit registration
    @rtype: datetime
    """
    if self.icSessionStart is not None:
      return self.icSessionStart

    times = map(attrgetter('Start'), self.__visits)
    try:
      return min(times)

    except ValueError:
      return None

  def getEnd(self):
    """
    @return: timestamp of the latest visit registration
    @rtype: datetime
    """
    if self.icSessionEnd is not None:
      return self.icSessionEnd

    times = map(attrgetter('End'), self.__visits)
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
    deprecated("Deprecated method getExcludedData() called; use getExcluded() instead.")
    return self.getExcluded()

  def getExcluded(self):
    return list(self.excluded)


#  def removeVisits(self, condition="False"):

# data management

  @staticmethod
  def _newNodes(nodes, cls=None):
    return map(cls.fromDict, nodes)

  def _insertLog(self, lNodes):
    self.__log = np.append(self.__log, self._newNodes(lNodes, LogNode))

  def _insertEnvironment(self, eNodes):
    self.__environment = np.append(self.__environment, self._newNodes(eNodes, EnvironmentNode))

  def _insertHardware(self, hNodes):
    self.__hardware = np.append(self.__hardware, self._newNodes(hNodes, HardwareEventNode))

  def _insertVisits(self, vNodes):
    vNodes = self._newNodes(vNodes, VisitNode) # callCopy might be faster but requires vNodes to be VisitNode-s
    for (vid, vNode) in enumerate(vNodes, start=len(self.__visits)):
      vNode._vid = vid

      animal = self.getAnimal(vNode.Animal)
      vNode.Animal = animal

      nosepokes = vNode.pop('Nosepokes', None)
      if self._getNp and nosepokes is not None:
        nosepokes = tuple(self._newNodes(nosepokes, NosepokeNode))
        vNode.Nosepokes = nosepokes
        for nid, npNode in enumerate(nosepokes, start=len(self.__nosepokes)):
          npNode.Visit = vNode
          npNode._nid = nid

        self.__nosepokes.extend(nosepokes)

      else:
        vNode.Nosepokes = None

    self.__visits = np.append(self.__visits, vNodes)
  
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

  def getAnimal(self, name=None, aid=None):
    """
    @param name: name of the animal
    @type name: basestring

    @param aid: internal ID of the animal
    @type aid: int

    @return: animal data if name or aid given else names of animals
    @rtype: AnimalNode if name or aid given else frozenset([unicode, ...])
    """
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
#  def _unregisterAnimal(self, Name = None, aid = None):

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

  def getChannel(self, mice=None, corner=None):
    visits = self.__visits
    if mice is not None:
      visits = self.__filterUnicode(visits, 'Animal', mice)

    if corner is not None:
      visits = self.__filterInt(visits, 'Corner', corner)

    return DataNode(Visits=list(visits))

  @staticmethod
  def _getTimeMask(time, startTime=None, endTime=None):
    mask = None
    if startTime is not None:
      mask = toTimestampUTC(startTime) <= time

    if endTime is not None:
      timeMask = toTimestampUTC(endTime) > time
      mask = timeMask if mask is None else mask * timeMask

    return mask

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

  def getVisits(self, mice=None, startTime=None, endTime=None, order=None):
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

    @param startTime: a lower bound of the visit Start attribute
    @type startTime: datetime

    @param endTime: an upper bound of the visit Start attribute
    @type endTime: datetime

    @param order: attributes that the returned list is ordered by
    @type order: str or (str, ...)

    @return: visits.
    @rtype: [VisitNode]
    """
    mask = None
    if mice is not None:
      try:
        mask = self.__animalVisits[mice]
        
      except (KeyError, TypeError): #unhashable type: list
        if isinstance(mice, basestring):
          mask = False

        else:
          mask = sum((self.__animalVisits[unicode(m)] for m in mice if unicode(m) in self.__animalVisits), False)

    timeMask = self._getTimeMask(self.__visitsStart, startTime, endTime)
    if timeMask is not None:
      mask = timeMask if mask is None else mask * timeMask

    if mask is False:
      return []

    visits = self.__visits if mask is None else self.__visits[mask]
    return self.__orderBy(visits, order)

  def getLogs(self, *args, **kwargs):
    """
    @deprecated: use L{getLog} instead.
    """
    deprecated("Obsolete method getLogs accessed.")
    return self.getLog(*args, **kwargs)

  def getLog(self, startTime=None, endTime=None, order=None):
    """
    >>> log = ml_icp3.getLog(order='DateTime')
    >>> for entry in log:
    ...   print entry.Notes
    Session is started
    Session is stopped

    @param startTime: a lower bound of the log entries DateTime attribute
    @type startTime: datetime

    @param endTime: an upper bound of the log entries DateTime attribute
    @type endTime: datetime

    @param order: attributes that the returned list is ordered by
    @type order: str or (str, ...)

    @return: log entries.
    @rtype: [LogNode, ...]
    """
    mask = self._getTimeMask(self.__logDateTime, startTime, endTime)
    log = self.__log if mask is None else self.__log[mask]
    return self.__orderBy(log, order)

  def getEnvironment(self, startTime=None, endTime=None, order=None):
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

    @param startTime: a lower bound of the sample DateTime attribute
    @type startTime: datetime

    @param endTime: an upper bound of the sample DateTime attribute
    @type endTime: datetime

    @param order: attributes that the returned list is ordered by
    @type order: str or (str, ...)

    @return: sampled environment conditions.
    @rtype: [EnvironmentNode, ...]
    """
    mask = self._getTimeMask(self.__envDateTime, startTime, endTime)
    env = list(self.__environment if mask is None else self.__environment[mask])
    return self.__orderBy(env, order)

  def getHardwareEvents(self, startTime=None, endTime=None, order=None):
    """
    @param startTime: a lower bound of the event DateTime attribute
    @type startTime: datetime

    @param endTime: an upper bound of the event DateTime attribute
    @type endTime: datetime

    @param order: attributes that the returned list is ordered by
    @type order: str or (str, ...)

    @return: hardware events.
    @rtype: [HardwareEventNode, ...]
    """
    mask = self._getTimeMask(self.__hwDateTime, startTime, endTime)
    hw = list(self.__hardware if mask is None else self.__hardware[mask])
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

    for log in self.__log:
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
      for log in self.__log:
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


def convertInt(x):
  return None if x == '' else int(x)


def convertStr(x):
  return None if x == '' else x


def fixSessions(data, sessions=[]):
  intervals = []
  end = None
  for session in sessions:
    start = session.Start
    if end is None:
      intervals.append((start, True))

    else:
      if end != start:
        intervals.append((end, False))
        intervals.append((start, True))

      else:
        intervals.append((start, True))

      if start < end:
        warnings.warn('Session overlap detected!')

      if start + start.utcoffset() <= end + end.utcoffset():
        warnings.warn('Session representations overlap, there is no hope. :-(')

    end = session.End
    if end is not None and end < start:
      warnings.warn("Negative session duration detected. Are you jocking, aren't you?")

  if end is not None:
    intervals.append((end, False))

  intervals = [([t.year, t.month, t.day,
                 t.hour, t.minute, t.second,
                 t.microsecond], t.tzinfo, t.utcoffset(), s) for t, s in intervals]
  intervals.append(None)
  lastTz = intervals[0][1]
  lastTo = intervals[0][2]

  dataQueue = timeListQueue(data)
  try:
    timepoint = dataQueue.next()
    lastTimepoint = timepoint
    tpDT = datetime(*timepoint)
    lastTpDt = tpDT
    delta = tpDT - lastTpDt
    zeroTd = delta
    hourTd = timedelta(seconds=3600)
    inSession = False
    for interval in intervals:
      if interval is not None:
        sentinel, tz, to, nextSession = interval

      offsetChange = to - lastTo
      tzChanged = offsetChange != zeroTd
      while timepoint <= sentinel or interval is None:
        if not inSession:
          print timepoint
          warnings.warn('Timepoints out of session!')

        if tzChanged:
          if lastTpDt > tpDT:
            if offsetChange > zeroTd:
              warnings.warn('Another candidate for tzchange')

            else:
              warnings.warn('Time not monotonic!')

          if offsetChange < zeroTd and delta > -offsetChange: #instead of abs
            warnings.warn('Another candidate for tzchange')

          timepoint.append(tz)

          # no check if there are other possibilities of change

        elif offsetChange > zeroTd and lastTpDt > tpDT:
          tzChanged = True
          timepoint.append(tz)

        elif offsetChange < zeroTd and delta > -offsetChange: #instead of abs
          tzChanged = True
          timepoint.append(tz)

        else:
          timepoint.append(lastTz)

        lastTimepoint = timepoint
        lastTpDt = tpDT
        timepoint = dataQueue.next()
        tpDT = datetime(*timepoint)
        delta = tpDT - lastTpDt

      lastTz = tz
      lastTo = to
      inSession = nextSession

  except StopIteration:
    pass


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
                 'IntelliCage/Visits': {'AnimalTag': 'Tag',
                                        'Animal': 'Tag', 
                                        'ID': '_vid',
                                        'VisitID': '_vid',
                                        'ModuleName': 'Module',
                                       },
                 'IntelliCage/Nosepokes': {'LicksNumber': 'LickNumber',
                                           'LicksDuration': 'LickDuration',
                                           'VisitID': '_vid',
                                          },
                 'IntelliCage/Log': {'LogType': 'Type',
                                     'Log': 'Type',
                                     'LogCategory': 'Category',
                                     'LogNotes': 'Notes',
                                    },
                 'IntelliCage/HardwareEvents': {'HardwareType': 'Type',
                                               },
                }
  _convertZip = {'Animals': {'Tag': int,
                             'Group': convertStr,
                             'Notes': convertStr,
                             'Sex': convertStr,
                            },
                 'IntelliCage/Visits': {'Tag': int,
                                        '_vid': int,
                                        'Start': timeToList,
                                        'End': timeToList,
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
                 'IntelliCage/Nosepokes': {'_vid': int,
                                           'Start': timeToList,
                                           'End': timeToList,
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
                 'IntelliCage/Log': {'DateTime': timeToList,
                                     #'Category': convertStr,
                                     #'Type': convertStr,
                                     #'Cage': convertInt,
                                     #'Corner': convertInt,
                                     #'Side': convertInt,
                                     #'Notes': convertStr,
                                    },
                 'IntelliCage/Environment': {'DateTime': timeToList,
                                             'Temperature': convertFloat,
                                             #'Illumination': convertInt,
                                             #'Cage': convertInt,
                                            },
                 'IntelliCage/HardwareEvents': {'DateTime': timeToList,
                                                #'Type': convertInt,
                                                #'Cage': convertInt,
                                                #'Corner': convertInt,
                                                #'Side': convertInt,
                                                #'State': convertInt,
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
        deprecated("Obsolete argument %s given for Loader constructor." % key)
        getNp = value

      elif key == 'getLogs':
        deprecated("Obsolete argument %s given for Loader constructor." % key)
        getLog = value

      elif key == 'getEnvironment':
        deprecated("Obsolete argument %s given for Loader constructor." % key)
        getEnv = value

      elif key in ('getHardware', 'getHardwareEvents'):
        deprecated("Obsolete argument %s given for Loader constructor." % key)
        getHw = value

      elif key == 'loganalyzers':
        logAnalyzers = value

      else:
        warnings.warn("Unknown argument %s given for Loader constructor." % key, stacklevel=2)

    if len(logAnalyzers) > 0:
      getLog = True

    Data.__init__(self, getNp=getNp, getLog=getLog, getEnv=getEnv, getHw=getHw)

    self._initCache()

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



  def _loadZip(self, fname, getNp=True, getLog=False, getEnv=False,
               getHw=False, source=None):
    if isinstance(fname, basestring) and os.path.isdir(fname):
      zf = PathZipFile(fname)

    else:
      zf = zipfile.ZipFile(fname)

    animalsLabels = set()
    animals = self._fromZipCSV(zf, 'Animals', oldLabels=animalsLabels)
    legacyFormat = 'Tag' in animalsLabels

    animalGroup = animals.pop('Group')
    animals = self._makeDicts(animals)

    animalNames = set()
    groups = {}
    tag2Animal = {}
    for group, animal in zip(animalGroup, animals):
      tag = animal['Tag']
      assert tag not in tag2Animal
      name = animal['Name']
      assert name not in animalNames
      tag2Animal[tag] = name
      animalNames.add(name)

      if group is not None:
        try:
          groups[group]['Animals'].append(name)

        except KeyError:
          groups[group] = {'Animals': [name],
                           'Name': group}

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
          warnings.warn(UserWarning('Timezone changed!'))

        for sessionStart, sessionEnd in sessions:
          if sessionEnd is None:
            continue

          if sessionStart < start < sessionEnd or\
             end is not None and sessionStart < end < sessionEnd or\
             (end is not None and start <= sessionStart and sessionEnd <= end) or\
             (end is not None and sessionStart <= start and end <= sessionEnd):
              warnings.warn(UserWarning('Temporal overlap of sessions!'))

        sessions.append(SessionNode(Start=start, End=end))

      sessions = sorted(sessions, key=attrgetter('Start'))

    except:
      sessions = None
      pass

    # timeToFix = []

    visits = self._fromZipCSV(zf, 'IntelliCage/Visits', source=source)
    tags = visits.pop('Tag')
    vids = visits.pop('_vid')

    if sessions is not None:
      vEnds = map(list, izip(visits['End'], repeat(1), repeat(None)))
      vStarts = map(list, izip(visits['Start'], repeat(0), vEnds)) # start blocks end
      timeToFix = [vEnds]
      visitStartOrder = np.argsort(vids)
      timeToFix.append(np.array(vStarts + [None], dtype=object)[visitStartOrder])

    else:
      timeToFix = visits['End'] + visits['Start'] 

    visits['Animal'] = map(tag2Animal.__getitem__, tags)
                     #[tag2Animal[tag] for tag in tags]

    orphans = []
    if getNp:
      visitNosepokes = [[] for vid in vids]
      vid2nps = dict(zip(vids, visitNosepokes))
      vid2tag = dict(zip(vids, tags))

      nosepokes = self._fromZipCSV(zf, 'IntelliCage/Nosepokes', source=source)

      npVids = nosepokes.pop('_vid')

      if sessions is not None:
        npEnds = map(list, izip(nosepokes['End'], repeat(True), repeat(None)))
        npStarts = map(list, izip(nosepokes['Start'], repeat(False), npEnds))
        npStarts = np.array(npStarts + [None], dtype=object)
        npTags = np.array(map(vid2tag.__getitem__, npVids))
        npSides = np.array(map(int, nosepokes['Side'])) % 2 # no bilocation assumed
        # XXX                   ^ - ugly... possibly duplicated

        timeToFix.append(npEnds)
        for tag in tag2Animal:
          for side in (0, 1): # tailpokes correction
            timeToFix.append(npStarts[(npTags == tag) * (npSides == side)])

      else:
        timeToFix.extend(nosepokes['End'])
        timeToFix.extend(nosepokes['Start'])

      nosepokes = self._makeDicts(nosepokes)
      #if sessions is not None:
      #  fixSessions(nosepokes, ['Start', 'End'], sessions)

      for vid, nosepoke in zip(npVids, nosepokes):
        try:
          vid2nps[vid].append(nosepoke)

        except KeyError:
          nosepoke['VisitID'] = vid
          orphans.append(nosepoke)

      # XXX!!!
      #map(methodcaller('sort', key=itemgetter('Start', 'End')),
      #    visitNosepokes)
      visits['Nosepokes'] = visitNosepokes


    else:
      visits['Nosepokes'] = [None] * len(tags)
      
    visits = self._makeDicts(visits)

    # XXX!!!
    #if sessions is not None:
    #  fixSessions(visits, ['Start', 'End'], sessions)

    result = {'animals': animals,
              'groups': groups.values(),
              'visits': visits,
              'nosepokes': orphans,
             }

    if getLog:
      log = self._fromZipCSV(zf, 'IntelliCage/Log', source=source)
      if sessions is not None:
        timeToFix.append(map(list, izip(log['DateTime'], repeat(False), repeat(None))))

      else:
        timeToFix.extend(log['DateTime'])

      log = self._makeDicts(log)

      #if sessions is not None:
      #  fixSessions(log, ['DateTime'], sessions)

      result['logs'] = log

    if getEnv:
      environment = self._fromZipCSV(zf, 'IntelliCage/Environment', source=source)
      if environment is not None:
        if sessions is not None:
          timeToFix.append(map(list, izip(environment['DateTime'], repeat(False), repeat(None))))

        else:
          timeToFix.extend(environment['DateTime'])

        environment = self._makeDicts(environment)
        #if sessions is not None:
        #  fixSessions(environment, ['DateTime'], sessions)

      else:
        environment = []

      result['environment'] = environment

    if getHw:
      hardware = self._fromZipCSV(zf, 'IntelliCage/HardwareEvents', source=source)
      if hardware is not None:
        if sessions is not None:
          timeToFix.append(map(list, izip(hardware['DateTime'], repeat(False), repeat(None))))

        else:
          timeToFix.extend(hardware['DateTime'])

        hardware = self._makeDicts(hardware)
        #if sessions is not None:
        #  fixSessions(hardware, ['DateTime'], sessions)

      else:
        hardware = []

      result['hardware'] = hardware

    #XXX important only when timezone changes!
    if sessions is not None:
      fixSessions(timeToFix, sessions)

    else:
      map(methodcaller('append', pytz.utc), timeToFix) # UTC assumed

    return result

  @staticmethod
  def _makeDicts(data):
    keys = data.keys()
    data = [data[k] for k in keys]
    return [dict(zip(keys, values)) for values in zip(*data)]


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
    
    #noneMapper = lambda x: x or None
    #data = map(lambda row: map(noneMapper, row), data)
    #data = [[x or None for x in row] for row in data]
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

  def appendData(self, fname):
    """
    Process one input file and append data to self.data
    """
    fname = fname.encode('utf-8') # stupid users!
    print 'loading data from %s' % fname
    #sid = self._registerSource(fname.decode('utf-8'))

    if fname.endswith('.zip') or os.path.isdir(fname):
      data = self._loadZip(fname,
                           getNp=self._getNp,
                           getLog=self._getLog,
                           getEnv=self._getEnv,
                           getHw=self._getHw,
                           source=fname.decode('utf-8'))
      animals = data['animals']
      groups = data['groups']
      visits = data['visits']
      orphans = data['nosepokes']

      if len(orphans) > 0:
        warnings.warn('Unmatched nosepokes: %s' % orphans)


      for animal in animals:
        self._registerAnimal(animal)

      for group in groups:
        self._registerGroup(**group)
        #members = group['Animals']
        #for animal in members:
        #  self._addMember(group['Name'], animal)

      self._insertVisits(visits)

      if self._getLog:
        self._insertLog(data['logs'])

      if self._getEnv:
        self._insertEnvironment(data['environment'])

      if self._getHw:
        self._insertHardware(data['hardware'])

      #self.loadZip(fname,
      #             sid = sid)

## Analyser data loading
#    else:
#      # Is that the right thing to do with directories?
#      if os.path.isdir(fname):
#        fname = os.path.join(fname, 'Visits.txt')
#
#      visits = self.fromCSV(fname, True)
#
#      startDate = visits.pop('StartDate')
#      startTime = visits.pop('StartTime')
#      #start = ['%s %s' % x for x in zip(startDate, startTime)]
#      #visits['Start'] = convertTime(start)
#      # Daylight saving time issue -_-
#
#      time0 = convertTime(startDate[0] + ' ' + startTime[0])
#      startTimecode = visits.pop('StartTimecode')
#      offset = time0 - float(startTimecode[0])
#      visits['Start'] = [offset + float(x) for x in startTimecode]
#
#      #endDate = visits.pop('EndDate')
#      #endTime = visits.pop('EndTime')
#      #end = ['%s %s' % x for x in zip(endDate, endTime)]
#      #visits['End'] = convertTime(end)
#      endTimecode = visits.pop('EndTimecode')
#      visits['End'] = [offset + float(x) for x in endTimecode]
#      del visits['EndDate']
#      del visits['EndTime']
#
#      del visits['VisitDuration'] # maybe some validation?
#      visits['ModuleName'] = visits.pop('Module')
#      animalTag = map(int, visits.pop('Tag'))
#      visits['AnimalTag'] = animalTag
#
#      ccMap = {'Neutral': 0.,
#               'Correct': 1.,
#               'Incorrect': -1.}
#
#      cc = visits['CornerCondition']
#      visits['CornerCondition'] = [(ccMap[c] if c in ccMap else convertFloat(c)) for c in cc]
#
#      aGroups = visits.pop('Group')
#      aNames = visits.pop('Animal')
#      aSexes = visits.pop('Sex')
#
#      # registering animals and groups
#      tag2aid = {}
#      for name, tag, sex in list(set(zip(aNames, animalTag, aSexes))):
#        if sex not in ('Male', 'Female', 'Unknown'):
#          print "Unknown sex: %s" % sex
#
#        animalNode = {'Name': name,
#                      'Tag': tag}
#        if sex != 'Unknown':
#          animalNode['Sex'] = sex
#
#        aid = self._registerAnimal(animalNode)
#        tag2aid[tag] = aid
#
#      group2gid = {}
#      for group in list(set(aGroups)):
#        self._registerGroup(group)
#
#      for tag, group in list(set(zip(animalTag, aGroups))):
#        aid = tag2aid[tag]
#        self._addMember(group, aid)
#
#      fakeNpokes = {}
#      fakeNpokes['VisitID'] = list(visits['VisitID'])
#      fakeNpokes['_line'] = list(visits['_line'])
#      fakeNpokes['SideError'] = visits.pop('SideErrors')
#      fakeNpokes['TimeError'] = visits.pop('TimeErrors')
#      fakeNpokes['ConditionError'] = visits.pop('ConditionErrors')
#      fakeNpokes['NosepokeNumber'] = visits.pop('NosepokeNumber')
#      fakeNpokes['NosepokeDuration'] = visits.pop('NosepokeDuration')
#      fakeNpokes['LickNumber'] = visits.pop('LickNumber')
#      fakeNpokes['LickDuration'] = visits.pop('LickDuration')
#      fakeNpokes['LickContactTime'] = visits.pop('LickContactTime')
#
#      vidMapping = self._insertVisits(visits, tag2aid, 'AnimalTag',
#                                      'VisitID', sid = sid)
#
#      if self._get_npokes:
#        self._insertNosepokes(fakeNpokes, vidMapping, 'VisitID', sid = sid)
#
#      try:
#        fh = open(os.path.join(os.path.dirname(fname),
#                               'Environment.txt'))
#        env = self.fromCSV(fh, True)
#        fh.close()
#
#        env['DateTime'] = convertTime(env['DateTime'])
#        self._insertDataSid(env, 'environment', sid)
#
#      except IOError:
#        print "'Environment.txt' not found."
#
#      try:
#        fh = open(os.path.join(os.path.dirname(fname),
#                               'Log.txt'))
#        self.loadLog(fh, sid=sid)
#
#      except IOError:
#        print "'Log.txt' not found."

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
  ...   print '%s %d %d' % (str(v.Animal), len(v.Nosepokes), v.Animal.Tag)
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
  ...   if isinstance(v.Animal.Tag, set):
  ...     print "  %s" % (', '.join(map(str, sorted(v.Animal.Tag))))
  ...   else:
  ...     print "  %d" % v.Animal.Tag
  Mickey 0
    42, 1337
  Minnie 1
    42, 1337
  Jerry 2
    69
  Minnie 1
    42, 1337
  Mickey 1
    42, 1337
  Jerry 2
    69
  """
  #TODO: common interface, not inheritance
  def __init__(self, *dataSources, **kwargs):
    """
    Usage: Merger(data_1, [data_2, ...] [parameters])

    @type data_X: Data

    @param getNp: whether to load nosepoke data (defaults to False).
    @type getNp: bool

    @param getLog: whether to load log (defaults to False).
    @type getLog: bool

    @param getEnv: whether to load environmental data (defaults to False).
    @type getEnv: bool

    @param getHw: whether to load hardware data (defaults to False).
    @type getHw: bool
    """
    getNp = kwargs.pop('getNp', True)
    getLog = kwargs.pop('getLog', False)
    getEnv = kwargs.pop('getEnv', False)
    getHw = kwargs.pop('getHw', False)
    logAnalyzers = kwargs.pop('logAnalyzers', [])

    for key, value in kwargs.items():
      if key in ('get_npokes', 'getNpokes', 'getNosepokes'):
        deprecated("Obsolete argument %s given for Merger constructor." % key)
        getNp = value

      elif key == 'getLogs':
        deprecated("Obsolete argument %s given for Merger constructor." % key)
        getLog = value

      elif key == 'getEnvironment':
        deprecated("Obsolete argument %s given for Merger constructor." % key)
        getEnv = value

      elif key in ('getHardware', 'getHardwareEvents'):
        deprecated("Obsolete argument %s given for Merger constructor." % key)
        getHw = value

      elif key == 'loganalyzers':
        deprecated("Obsolete argument %s given for Merger constructor." % key)
        logAnalyzers = value

      else:
        warnings.warn("Unknown argument %s given for Merger constructor" % key, stacklevel=2)

    if len(logAnalyzers) > 0:
      getLog = True

    Data.__init__(self, getNp=getNp, getLog=getLog, getEnv=getEnv, getHw=getHw)

    self._dataSources = map(str, dataSources)

    self._initCache()
    self.__topTime = datetime(MINYEAR, 1, 1, tzinfo=pytz.timezone('Etc/GMT-14'))

    for dataSource in dataSources:
      try:
        self.appendDataSource(dataSource)

      except:
        print "ERROR processing %s" % dataSource
        raise

    self._logAnalysis(logAnalyzers)

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
    for attr in ['Start', 'End']:
      icAttr = 'icSession' + attr
      vals = [x for x in [getattr(self, icAttr),
                          getattr(dataSource, 'get' + attr)()] if x is not None]
      if len(vals) > 0:
        setattr(self, icAttr, min(vals))

    # registering animals and groups (if necessary)
    for name in dataSource.getAnimal():
      animal = dataSource.getAnimal(name)
      self._registerAnimal(animal)


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

      self._insertVisits(visits)

    if self._getHw:
      hardware = dataSource.getHardwareEvents()
      if hardware is not None:
        self._insertHardware(hardware)

    if self._getEnv:
      env = dataSource.getEnvironment()
      if env is not None:
        self._insertEnvironment(env)

    if self._getLog:
      log = dataSource.getLog()
      if log is not None:
        self._insertLog(log)

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



if __name__ == '__main__':
  import doctest
  testDir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../test'))
  TEST_GLOBALS = {
    #XXX: ml_l1 - not sure if data formad is valid
    'ml_l1': Loader(os.path.join(testDir, 'legacy_data.zip')),
    #'ml_a1': Loader(os.path.join(testDir, 'analyzer_data.txt'), getNpokes=True),
    'ml_icp3': Loader(os.path.join(testDir, 'icp3_data.zip'),
                      getLogs=True, getEnv=True),
    'ml_empty': Loader(os.path.join(testDir, 'empty_data.zip')),
    'ml_retagged': Loader(os.path.join(testDir, 'retagged_data.zip')),
    }

  doctest.testmod(extraglobs=TEST_GLOBALS)
