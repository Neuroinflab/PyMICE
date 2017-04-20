#!/usr/bin/env python
# encoding: utf-8
###############################################################################
#                                                                             #
#    PyMICE library                                                           #
#                                                                             #
#    Copyright (C) 2015-2017 Jakub M. Dzik a.k.a. Kowalski, S. Łęski          #
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

import os
import shutil
import sys

from ._Tools import isString


class FetchStdoutReporter(object):
  def warnUnknownDataset(self, dataset):
    sys.stderr.write(u'Warning: unknown download requested ({})\n'.format(dataset))

  def reportUnnecessaryFetch(self, dataset):
    sys.stderr.write(u'{} dataset already present\n'.format(dataset))

  def reportNothingToFetch(self):
    sys.stderr.write(u'All datasets already present.\n')


class FetchDummyReporter(object):
  def __getattribute__(self, attribute):
    def dummyFunction(*args, **kwargs):
      return None

    return dummyFunction


class DataGetter(object):
  DATA = {'C57_AB': {'C57_AB/2012-08-28 13.44.51.zip': 86480,
                     'C57_AB/2012-08-28 15.33.58.zip': 494921,
                     'C57_AB/2012-08-31 11.46.31.zip': 29344,
                     'C57_AB/2012-08-31 11.58.22.zip': 3818445,
                     'C57_AB/timeline.ini': 2894,
                     'C57_AB/COPYING': 709,
                     'C57_AB/LICENSE': 19467,
                    },
          'demo': {'demo.zip': 106091,
                   'COPYING': 552,
                   'LICENSE': 19467,
                   },
          'FVB': {'FVB/2016-07-20 10.11.11.zip': 931977,
                  'FVB/COPYING': 601,
                  'FVB/LICENSE': 19467,
                  'FVB/timeline.ini': 1040,},
         }

  def __init__(self, path, reporter):
    self.setPath(path)
    self._reporter = reporter

  def setPath(self, path):
    if path is None:
      path = os.getcwd()

    self.ensureIsDirectory(path)
    self._path = path

  def ensureIsDirectory(self, path):
    if not os.path.exists(path):
      os.makedirs(path)

    elif not os.path.isdir(path):
      raise OSError("Not a directory: '{}'".format(path))

  def necessaryDataSetsGenerator(self, fetch):
    for dataset in fetch:
      if self.isFetchPossibleAndNecessary(dataset):
        yield dataset

  def isFetchPossibleAndNecessary(self, dataset):
    try:
      files = self.DATA[dataset]

    except KeyError:
      self._reporter.warnUnknownDataset(dataset)
      return

    if all(self.fileSizeMatches(fn, fs) for (fn, fs) in files.items()):
      self._reporter.reportUnnecessaryFetch(dataset)
      return

    return True

  def fileSizeMatches(self, filename, size):
    path = os.path.join(self._path, filename)
    return os.path.isfile(path) and os.path.getsize(path) == size

  def fetch(self, requested):
    if requested is None:
      requested = sorted(self.DATA.keys())

    elif isString(requested):
      requested = (requested,)

    toFetch = list(self.necessaryDataSetsGenerator(requested))

    if not toFetch:
      self._reporter.reportNothingToFetch()
      return

    self.fetchDatasets(toFetch)

  def fetchDatasets(self, datasets):
    for dataset in datasets:
      self.fetchDataset(dataset)


class ModuleDataGetter(DataGetter):
  PATHS = {'C57_AB': ['tutorial/C57_AB',],
           'demo': ['tutorial/demo.zip',
                    'tutorial/LICENSE',
                    'tutorial/COPYING',],
           'FVB': ['tutorial/FVB',],
           }



  def fetchDataset(self, dataset):
    for path in self.PATHS[dataset]:
      self.fetchDir(path)

  def fetchDir(self, path):
    src = os.path.join(os.path.dirname(__file__), 'data', path)
    self.copyFiles(src, self._path)

  def copyFiles(self, src, dst):
    if os.path.isdir(src):
      path = os.path.join(dst, os.path.basename(src))
      if not os.path.exists(path):
        os.mkdir(path)

      for item in os.listdir(src):
        self.copyFiles(os.path.join(src, item),
                       path)

    else:
      shutil.copy(src, dst)


def getTutorialData(path=None, quiet=False, fetch=None):
  """
  Write to disk example dataset(s) used in tutorials.

  :param path: a directory where tutorial data are to be loaded into
               (defaults to working directory)
  :type path: basestring

  :param quiet: a switch disabling stdout output.
  :type quiet: bool

  :param fetch: the datasets to download
  :type fetch: collection(basestring, ...)



  """
  downloader = ModuleDataGetter(path, FetchDummyReporter() if quiet else FetchStdoutReporter())
  downloader.fetch(fetch)