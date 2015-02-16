#!/usr/bin/env python
# encoding: utf-8
"""
_Loader.py

Copyright (c) 2012-2014 Laboratory of Neuroinformatics. All rights reserved.
"""

import sys
import os
import time

import dateutil.parser

import zipfile
import csv
import warnings
import operator

from xml.dom import minidom

try:
  from ._Data import Data
  from ._Tools import deprecated, convertTime

except ValueError:
  try:
    print "from .<XXX> import... failed"
    from PyMICE._Data import Data
    from PyMICE._Tools import deprecated, convertTime

  except ImportError:
    print "from PyMICE.<XXX> import... failed"
    from _Data import Data
    from _Tools import deprecated, convertTime

try:
  from PyMICE._C import emptyStringToNone

except Exception as e:
  print type(e), e

  def emptyStringToNone(l):
    for i, x in enumerate(l):
      if type(x) is list:
        emptyStringToNone(x)

      elif x == '':
        l[i] = None

    return l



#def convertFloat(x):
#  return None if x == '' else float(x.replace(',', '.'))

convertFloat = operator.methodcaller('replace', ',', '.')

def convertInt(x):
  return None if x == '' else int(x)


def convertStr(x):
  return None if x == '' else x


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
                                        'Start': convertTime,
                                        'End': convertTime,
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
                                           'Start': convertTime,
                                           'End': convertTime,
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
                 'IntelliCage/Log': {'DateTime': convertTime,
                                     #'Category': convertStr,
                                     #'Type': convertStr,
                                     #'Cage': convertInt,
                                     #'Corner': convertInt,
                                     #'Side': convertInt,
                                     #'Notes': convertStr,
                                    },
                 'IntelliCage/Environment': {'DateTime': convertTime,
                                             'Temperature': convertFloat,
                                             #'Illumination': convertInt,
                                             #'Cage': convertInt,
                                            },
                 'IntelliCage/HardwareEvents': {'DateTime': convertTime,
                                                #'Type': convertInt,
                                                #'Cage': convertInt,
                                                #'Corner': convertInt,
                                                #'Side': convertInt,
                                                #'State': convertInt,
                                               },
                }

  def __init__(self, fname, getNp=False, getLog=False, getEnv=False, getHw=False,
               logAnalyzers=(), **kwargs):
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



  def _loadZip(self, fname, getNp=False, getLog=False, getEnv=False,
               getHw=False, source=None):
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
        end = dateutil.parser.parse(end.nodeValue)
        if start.tzinfo != end.tzinfo:
          warnings.warn(UserWarning('Timezone changed!'))

        for sessionStart, sessionEnd in sessions:
          if sessionStart < start < sessionEnd or\
             sessionStart < end < sessionEnd or\
             (start <= sessionStart and sessionEnd <= end) or\
             (sessionStart <= start and end <= sessionEnd):
              warnings.warn(UserWarning('Temporal overlap of sessions!'))

        sessions.append((start, end))

      sessions = sorted(sessions)

    except:
      sessions = None
      pass

    visits = self._fromZipCSV(zf, 'IntelliCage/Visits', source=source)
    tags = visits.pop('Tag')
    vids = visits.pop('_vid')

    visits['Animal'] = [tag2Animal[tag] for tag in tags]

    orphans = []
    if getNp:
      visitNosepokes = [[] for vid in vids]
      vid2nps = dict(zip(vids, visitNosepokes))

      nosepokes = self._fromZipCSV(zf, 'IntelliCage/Nosepokes', source=source)
      npVids = nosepokes.pop('_vid')

      nosepokes = self._makeDicts(nosepokes)
      for vid, nosepoke in zip(npVids, nosepokes):
        try:
          vid2nps[vid].append(nosepoke)

        except KeyError:
          nosepoke['VisitID'] = vid
          orphans.append(nosepoke)

      map(operator.methodcaller('sort',
                                key=operator.itemgetter('Start', 'End')),
          visitNosepokes)
      visits['Nosepokes'] = visitNosepokes


    else:
      visits['Nosepokes'] = [None] * len(tags)
      
    visits = self._makeDicts(visits)
    result = {'animals': animals,
              'groups': groups.values(),
              'visits': visits,
              'nosepokes': orphans,
             }

    if getLog:
      logs = self._fromZipCSV(zf, 'IntelliCage/Log', source=source)
      result['logs'] = self._makeDicts(logs)

    if getEnv:
      environment = self._fromZipCSV(zf, 'IntelliCage/Environment', source=source)
      result['environment'] = self._makeDicts(environment)

    if getHw:
      hardware = self._fromZipCSV(zf, 'IntelliCage/HardwareEvents', source=source)
      result['hardware'] = self._makeDicts(hardware)

    return result

  @staticmethod
  def _makeDicts(data):
    keys = data.keys()
    data = [data[k] for k in keys]
    return [dict(zip(keys, values)) for values in zip(*data)]


  def _fromZipCSV(self, zf, path, source=None, oldLabels=None):
    return self._fromCSV(zf.open(path + '.txt'), source=source,
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

    if fname.endswith('.zip'):
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
  def convert_time(ll):
    print "WARNING: Deprecated method convert_time() called."
    return convertTime(ll)

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


if __name__ == '__main__':
  import doctest
  try:
    from _test import TEST_GLOBALS

  except ImportError:
    print "from _test import... failed"
    from PyMICE._test import TEST_GLOBALS

  doctest.testmod(extraglobs=TEST_GLOBALS)
