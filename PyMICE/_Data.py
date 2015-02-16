#!/usr/bin/env python
# encoding: utf-8
"""
_Data.py

Copyright (c) 2012-2014 Laboratory of Neuroinformatics. All rights reserved.
"""

import sys
import os
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.path import Path
import zipfile
import csv
import cStringIO
import copy
import numpy as np
from operator import itemgetter, methodcaller, attrgetter
from ICNodes import DataNode, AnimalNode, GroupNode, VisitNode, NosepokeNode,\
                    LogNode, EnvironmentNode, HardwareEventNode

from _Tools import timeString, deprecated, ensureFloat, ensureInt, hTime

callCopy = methodcaller('copy')


class Data(object):
  """
  A base class for objects containing behavioural data.
  """
  def __init__(self, getNp=False, getLog=False,
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
        print "WARNING: Animal %s found in multiple cages (%s)." %\
              (animal, ', '.join(map(str, self.__animal2cage[animal])))

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
    self.__visitsStart = np.array(map(float, map(attrgetter('Start'),
                                                 self.__visits)))

    if self._getLog:
      self.__logDateTime = np.array(map(float, map(attrgetter('DateTime'),
                                                   self.__log)))

    if self._getEnv:
      self.__envDateTime = np.array(map(float, map(attrgetter('DateTime'),
                                                   self.__environment)))

    if self._getHw:
      self.__hwDateTime = np.array(map(float, map(attrgetter('DateTime'),
                                                   self.__hardware)))

  def getCage(self, mouse):
    """
    """
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
    return frozenset(self.__animalsByName)

  def getInmates(self, cage = None):
    if cage == None:
      return frozenset(self.__cages)

    return self.__cages[cage] # is a frozenset already

#  def getFirstLick(self, corners = (), mice=()):

  def getStart(self):
    if self.icSessionStart is not None:
      return self.icSessionStart

    times = map(attrgetter('Start'), self.__visits)
    try:
      return min(times)

    except ValueError:
      return None

  def getEnd(self):
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
    print "WARNING: deprecated method getExcludedData() called."
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
      mask = startTime <= time

    if endTime is not None:
      timeMask = endTime > time
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
    ...   print hTime(v.Start)
    2012-12-18 12:13:14.139
    2012-12-18 12:18:55.421
    2012-12-18 12:19:55.421

    >>> for v in ml_l1.getVisits(mice='Minnie'):
    ...   print hTime(v.Start)
    2012-12-18 12:30:02.360

    @param startTime: a lower bound of the visit Start attribute given
                      as a timestamp (epoch).
    @type startTime: float

    @param endTime: an upper bound of the visit Start attribute given
                    as a timestamp (epoch).
    @type endTime: float

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
        mask = sum((self.__animalVisits[m] for m in mice), False)

    timeMask = self._getTimeMask(self.__visitsStart, startTime, endTime)
    if timeMask is not None:
      mask = timeMask if mask is None else mask * timeMask

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

    @param startTime: a lower bound of the log entries DateTime attribute given
                      as a timestamp (epoch).
    @type startTime: float

    @param endTime: an upper bound of the log entries DateTime attribute given
                    as a timestamp (epoch).
    @type endTime: float

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

    @param startTime: a lower bound of the sample DateTime attribute given
                      as a timestamp (epoch).
    @type startTime: float

    @param endTime: an upper bound of the sample DateTime attribute given
                    as a timestamp (epoch).
    @type endTime: float

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
    @param startTime: a lower bound of the event DateTime attribute given
                      as a timestamp (epoch).
    @type startTime: float

    @param endTime: an upper bound of the event DateTime attribute given
                    as a timestamp (epoch).
    @type endTime: float

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

if __name__ == '__main__':
  import doctest
  try:
    from _test import TEST_GLOBALS

  except ImportError:
    print "from _test import... failed"
    from PyMICE._test import TEST_GLOBALS

  doctest.testmod(extraglobs=TEST_GLOBALS)
