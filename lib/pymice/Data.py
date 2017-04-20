#!/usr/bin/env python
# encoding: utf-8
###############################################################################
#                                                                             #
#    PyMICE library                                                           #
#                                                                             #
#    Copyright (C) 2012-2017 Jakub M. Dzik a.k.a. Kowalski, S. Łęski          #
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

import sys
if sys.version_info >= (3, 0):
  unicode = str

import os
import zipfile
import csv
try:
  import cStringIO as io

except ImportError:
  import io

from operator import methodcaller, attrgetter
from collections import Container

from .ICNodes import Group # XXX: unnecessary dependency

from ._Tools import timeString, toTimestampUTC, warn, isString
from ._ObjectBase import ObjectBase


class IdentityManager(object):
  def __getitem__(self, x):
    return x


class IntIdentityManager(int):
  def __new__(cls, *args, **kwargs):
    if len(args) + len(kwargs) == 0:
      args = [0]

    return int.__new__(cls, *args, **kwargs)

  def __getitem__(self, x):
    return self.__class__(x)

  def _del_(self):
    pass


class Data(object):
  """
  A base class for objects containing behavioural data.
  """

  def __init__(self, getNp=True, getLog=False,
               getEnv=False, getHw=False,
               SourceManager=IdentityManager,
#               CageManager=IntIdentityManager,
               AnimalManager=dict):
    """
    :param getNp: whether to load nosepoke data.
    :type getNp: bool

    :param getLog: whether to load log.
    :type getLog: bool

    :param getEnv: whether to load environmental data.
    :type getEnv: bool

    :param getHw: whether to load hardware data.
    :type getHw: bool
    """
    self.__name2group = {}

    self._getNp = getNp
    self._getLog = getLog
    self._getEnv = getEnv
    self._getHw = getHw

    self.__frozen = False

    # change to
    self.__animalsByName = AnimalManager()

    self.__visits = ObjectBase({
      'Start': toTimestampUTC,
      'End': toTimestampUTC})

    self.__log = ObjectBase({'DateTime': toTimestampUTC})
    self.__environment = ObjectBase({'DateTime': toTimestampUTC})
    self.__hardware = ObjectBase({'DateTime': toTimestampUTC})
    self._initCache()

#    self._setCageManager(CageManager())
    self._sourceManager = SourceManager()

  def _setCageManager(self, cageManager):
    self._cageManager = cageManager

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

  def getVisits(self, mice=None, start=None, end=None, order=None):
    """
    :param mice: mouse (or mice) which visits are requested
    :type mice: str or unicode or :py:class:`Animal` or collection of them or None

    :param start: a lower bound of the visit Start attribute
    :type start: datetime.datetime or None

    :param end: an upper bound of the visit Start attribute
    :type end: datetime.datetime or None

    :param order: attributes that the returned list is ordered by
    :type order: str or unicode or their sequence or None

    :return: visits
    :rtype: [:py:class:`Visit`, ...]

    >>> data.getVisits(mice='Mickey')
    [< Visit of "Mickey" to corner #1 of cage #1 (at 2012-12-18 12:31:00.000) >]

    >>> data.getVisits(mice=['Mickey', 'Minnie'], order='Start')
    [< Visit of "Minnie" to corner #4 of cage #1 (at 2012-12-18 12:30:02.360) >,
     < Visit of "Mickey" to corner #1 of cage #1 (at 2012-12-18 12:31:00.000) >]

    >>> mice = [data.getAnimal(m) for m in ['Mickey', 'Minnie']]
    >>> data.getVisits(mice=mice, order='Start')
    [< Visit of "Minnie" to corner #4 of cage #1 (at 2012-12-18 12:30:02.360) >,
     < Visit of "Mickey" to corner #1 of cage #1 (at 2012-12-18 12:31:00.000) >]
    """
    selectors = self.__makeTimeSelectors('Start', start, end)
    if mice is not None:
      if isString(mice) or not isinstance(mice, Container):
        mice = [mice]

      selectors['Animal.Name'] = map(unicode, mice)

    visits = self.__visits.get(selectors)
    return self.__orderBy(visits, order)

  def getLog(self, start=None, end=None, order=None):
    """
    :param start: a lower bound of the log entries DateTime attribute
    :type start: datetime.datetime or None

    :param end: an upper bound of the log entries DateTime attribute
    :type end: datetime.datetime or None

    :param order: attributes that the returned list is ordered by
    :type order: str or unicode or their sequence or None

    :return: log entries
    :rtype: [:py:class:`LogEntry`, ...]

    >>> data.getLog(order='DateTime')
    [< Log Info, Application (at 2012-12-18 12:13:02.437) >,
     < Log Info, Application (at 2012-12-18 12:20:37.718) >]
    """
    selectors = self.__makeTimeSelectors('DateTime', start, end)
    log = self.__log.get(selectors)
    return self.__orderBy(log, order)

  def getEnvironment(self, start=None, end=None, order=None):
    """
    :param start: a lower bound of the sample DateTime attribute
    :type start: datetime.datetime or None

    :param end: an upper bound of the sample DateTime attribute
    :type end: datetime.datetime or None

    :param order: attributes that the returned list is ordered by
    :type order: str or unicode or their sequence or None

    :return: sampled environment conditions
    :rtype: [:py:class:`EnvironmentalConditions`, ...]

    >>> data.getEnvironment(order=('DateTime', 'Cage'))
    [< Illumination:   0, Temperature: 22.0 (at 2012-12-18 12:13:02.000) >,
     < Illumination:   0, Temperature: 23.6 (at 2012-12-18 12:13:02.000) >,
     < Illumination:   0, Temperature: 22.0 (at 2012-12-18 12:14:02.000) >,
     < Illumination:   0, Temperature: 23.6 (at 2012-12-18 12:14:02.000) >,
     < Illumination:   0, Temperature: 22.0 (at 2012-12-18 12:15:02.000) >,
     < Illumination:   0, Temperature: 23.6 (at 2012-12-18 12:15:02.000) >,
     < Illumination:   0, Temperature: 22.0 (at 2012-12-18 12:16:02.000) >,
     < Illumination:   0, Temperature: 23.6 (at 2012-12-18 12:16:02.000) >,
     < Illumination:   0, Temperature: 22.0 (at 2012-12-18 12:17:02.000) >,
     < Illumination:   0, Temperature: 23.6 (at 2012-12-18 12:17:02.000) >,
     < Illumination:   0, Temperature: 22.0 (at 2012-12-18 12:18:02.000) >,
     < Illumination:   0, Temperature: 23.6 (at 2012-12-18 12:18:02.000) >,
     < Illumination:   0, Temperature: 22.0 (at 2012-12-18 12:19:02.000) >,
     < Illumination:   0, Temperature: 23.6 (at 2012-12-18 12:19:02.000) >,
     < Illumination:   0, Temperature: 22.0 (at 2012-12-18 12:20:02.000) >,
     < Illumination:   0, Temperature: 23.6 (at 2012-12-18 12:20:02.000) >]
    """
    selectors = self.__makeTimeSelectors('DateTime', start, end)
    env = self.__environment.get(selectors)
    return self.__orderBy(env, order)

  def getHardwareEvents(self, start=None, end=None, order=None):
    """
    :param start: a lower bound of the event DateTime attribute
    :type start: datetime.datetime or None

    :param end: an upper bound of the event DateTime attribute
    :type end: datetime.datetime or None

    :param order: attributes that the returned list is ordered by
    :type order: str or unicode or their sequence or None

    :return: hardware events
    :rtype: [:py:class:`HardwareEvent`, ...]
    """
    selectors = self.__makeTimeSelectors('DateTime', start, end)
    hw = self.__hardware.get(selectors)
    return self.__orderBy(hw, order)

  def getCage(self, mouse):
    """
    :param mouse: mouse name or representation
    :type mouse: basestring or :py:class:`Animal`

    :return: cage(s) where mouse's visits has been registered
    :rtype: convertable to int or (convertable to int, ...)

    >>> data.getCage('Minnie')
    1

    >>> data.getCage(data.getAnimal('Minnie'))
    1
    """
    try:
      cages = self.__animal2cage[unicode(mouse)]

    except KeyError:
      warn.warn("Mouse {} not found in any cage.".format(mouse),
                stacklevel=2)
      return None

    if len(cages) != 1:
      warn.warn("Mouse %s found in multiple cages: %s." \
                % (mouse, ', '.join(map(str, cages))), stacklevel=2)
      return tuple(cages)

    return cages[0]

  def getMice(self):
    """
    :return: names of registered animals
    :rtype: frozenset(unicode, ...)
    """
    return frozenset(self.__animalsByName)

  def getInmates(self, cage=None):
    """
    :param cage: number of the cage
    :type cage: convertable to int or None

    :return: animals detected in the cage if given else available cages
    :rtype:  frozenset(:py:class:`Animal`, ...) if cage is given
             else frozenset(int, ...)
    """
    if cage == None:
      return frozenset(self.__cages)

    return self.__cages[int(cage)] # is a frozenset already

  def getStart(self):
    """
    :return: time of the earliest visit registration
    :rtype: datetime.datetime or None
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
    :return: time of the latest visit registration
    :rtype: datetime.datetime or None
    """
    if self.icSessionEnd is not None:
      return self.icSessionEnd

    times = self.__visits.getAttributes('End')
    try:
      return max(times)

    except ValueError:
      return None

  def getGroup(self, name=None):
    """
    :param name: name of the group
    :type name: basestring or None

    :return: group data if name given else names of groups
    :rtype: :py:class:`Group` if name given else frozenset([unicode, ...])
    """
    if name != None:
      return self.__name2group[name]

    return frozenset(self.__name2group)

  def getAnimal(self, name=None):
    """
    :param name: name of the animal
    :type name: unicode convertable or None

    :return: animal data if name given else names of animals
    :rtype: :py:class:`Animal` if name given else frozenset([unicode, ...])
    """
    if name is not None:
      return self.__animalsByName[unicode(name)]

    return frozenset(self.__animalsByName)


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


# data management
  def insertLog(self, log):
    self._raiseIfFrozen()

    newLog = self.__cloneObjectsWithSourceCageManagers(log)
    self._insertNewLog(newLog)

  def _insertNewLog(self, lNodes):
    self.__log.put(lNodes)

  def insertEnv(self, env):
    self._raiseIfFrozen()

    newEnv = self.__cloneObjectsWithSourceCageManagers(env)
    self._insertNewEnv(newEnv)

  def _insertNewEnv(self, eNodes):
    self.__environment.put(eNodes)

  def insertHw(self, hardwareEvents):
    self._raiseIfFrozen()

    newHw = self.__cloneObjectsWithSourceCageManagers(hardwareEvents)
    self._insertNewHw(newHw)

  def _insertNewHw(self, hNodes):
    self.__hardware.put(hNodes)

  def freeze(self):
    self.__frozen = True

  def _raiseIfFrozen(self):
    if self.__frozen:
      raise self.UnableToInsertIntoFrozen

  def __cloneObjectsWithSourceCageManagers(self, objects):
    return map(methodcaller('clone', self._sourceManager,
                            self._cageManager),
               objects)

  def insertVisits(self, visits):
    self._raiseIfFrozen()

    newVisits = map(methodcaller('clone', self._sourceManager,
                                 self._cageManager,
                                 self.__animalsByName),
                    visits)
    self._insertNewVisits(newVisits)

  def _insertNewVisits(self, visits):
    self.__visits.put(visits)

  def _registerGroup(self, Name, Animals=[], **kwargs):
    Animals = [self.getAnimal(animal) for animal in Animals] # XXX sanity
    if Name in self.__name2group:
      group = self.__name2group[Name]
      group.merge(Name=Name, Animals=Animals, **kwargs)
      return group

    group = Group(Name=Name, Animals=Animals, **kwargs)
    self.__name2group[Name] = group
    return group

  def _addMember(self, name, animal):
    group = self.__name2group[name]
    animal = self.getAnimal(animal) # XXX sanity
    group.addMember(animal)

  def _registerAnimal(self, aNode):
    try:
      animal = self.__animalsByName[aNode.Name]

    except KeyError:
      animal = aNode.clone()
      self.__animalsByName[animal.Name] = animal

    else:
      animal.merge(aNode)

    return animal

  @staticmethod
  def __orderBy(data, order):
    if order is None:
      return list(data)

    key = attrgetter(order) if isString(order) else attrgetter(*order)
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

  class UnableToInsertIntoFrozen(TypeError):
    pass

  def _save(self, filename, force=False):
    """
    An experimental method for saving the data.

    :param filename: path to the file data has to be saved to; if filename does
                     not end with '.zip', the suffix is being appended.
    :type filename: basestring

    :param force: whether to overwrite an existing file
    :type force: bool
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

# # TO BE MOVED TO DEBUG MODULE
#import matplotlib.pyplot as plt
#import matplotlib.patches as patches
#from matplotlib.path import Path
#   def _plotMiceCage(self):
#     visits = {}
#     for v in self.getVisits():
#       try:
#         visits[unicode(v.Animal)].append((v.Start, int(v.Cage)))
#
#       except KeyError:
#         visits[unicode(v.Animal)] = [(v.Start, int(v.Cage))]
#
#     for mouse, data in visits.items():
#       cages = []
#       times = []
#       data.sort()
#       lastC, lastT = None, None
#       many = False
#       for t, c in data:
#         if c != lastC:
#           if many:
#             cages.append(lastC)
#             times.append(lastT)
#
#           many = False
#           cages.append(c)
#           times.append(t)
#           lastC = c
#
#         else:
#           many = True
#           lastT = t
#
#       if many:
#         cages.append(lastC)
#         times.append(lastT)
#
#       plt.plot(times, cages, label=mouse)
#
#       #plt.legend()
#
#   def _plotChannel(self, top=1., bottom=0., startM=None, endM=None):
#     #TODO!!!!
#     h = top - bottom
#     data = self.getVisits()
#     startD = min(map(attrgetter('Start'), data))
#     endD = max(map(attrgetter('End'), data))
#     startR = self.icSessionStart
#     endR = self.icSessionEnd
#
#     ax = plt.gca()
#
#     if endD is not None and startD is not None: # imagine case when only one is true -_-
#       htop = 0.75 * top + 0.25 * bottom
#       hbottom = 0.25 * top + 0.75 * bottom
#       path = Path([(startD, htop), (endD, htop), (endD, hbottom), (startD, hbottom), (startD, htop)],
#                   [Path.MOVETO, Path.LINETO, Path.LINETO, Path.LINETO, Path.CLOSEPOLY])
#       patch = patches.PathPatch(path, facecolor='green', edgecolor='green')
#       ax.add_patch(patch)
#
#     if startR is not None or endR is not None:
#       medium = 0.5 * (top + bottom)
#       left = startR if startR is not None else startD if startD is not None else startM
#       right = endR if endR is not None else endD if endD is not None else endM
#       path = Path([(left, medium), (right, medium)], [Path.MOVETO, Path.LINETO])
#       patch = patches.PathPatch(path, facecolor='none', edgecolor='black')
#       ax.add_patch(patch)
#
#     if startM is not None or endM is not None:
#       verts = []
#       codes = []
#       left = startM if startM is not None else startR if startR is not None else startD
#       right = endM if endM is not None else endR if endR is not None else endD
#
#       codes.append(Path.MOVETO)
#       verts.append((left, top))
#       codes.append(Path.LINETO)
#       verts.append((right, top))
#       codes.append(Path.LINETO if endM is not None else Path.MOVETO)
#       verts.append((right, bottom))
#       codes.append(Path.LINETO)
#       verts.append((left, bottom))
#       if startM is not None:
#         verts.append((left, top))
#         codes.append(Path.CLOSEPOLY)
#
#       path = Path(verts, codes)
#       patch = patches.PathPatch(path, facecolor='none', edgecolor='red')
#       ax.add_patch(patch)
#
#     times = [x for x in [startD, endD, startR, endR, startM, endM] if x is not None]
#     return min(times), max(times)
#
#   def _plotChannelR(self, top=1., bottom=0.):
#     # to be overriden
#     return self.plotChannel(top=top, bottom=bottom)
