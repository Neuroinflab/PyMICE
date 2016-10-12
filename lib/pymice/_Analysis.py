#!/usr/bin/env python
# encoding: utf-8
###############################################################################
#                                                                             #
#    PyMICE library                                                           #
#                                                                             #
#    Copyright (C) 2016 Jakub M. Kowalski (Laboratory of Neuroinformatics;    #
#    Nencki Institute of Experimental Biology of Polish Academy of Sciences)  #
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

from ._Ens import Ens

class Analyser(object):
  class Results(object):
    class CircularDependencyError(RuntimeError):
      pass

    class UnknownDependencyError(RuntimeError):
      pass

    def __init__(self, data, analysers):
      self.__data = data
      self.__analysers = dict(analysers)
      self.__lock = set()
      self.__values = {}

    def __getattr__(self, name):
      try:
        return self.__values[name]

      except KeyError:
        return self.__createAttribute(name)

    def __createAttribute(self, name):
      self.__ensureNoPreviousAttemptsToCreate(name)
      return self.__calculateAndStoreAttribute(name)

    def __ensureNoPreviousAttemptsToCreate(self, item):
      if item in self.__lock:
        raise self.CircularDependencyError

      self.__lock.add(item)

    def __calculateAndStoreAttribute(self, name):
      value = self.__callAnalyser(self.__getAnalyser(name))
      self.__values[name] = value
      return value

    def __getAnalyser(self, item):
      try:
        return self.__analysers[item]

      except KeyError:
        raise self.UnknownDependencyError

    def __callAnalyser(self, analyser):
      try:
        return analyser(self.__data)

      except TypeError:
        return analyser(self, self.__data)

  def __init__(self, **analysers):
    self.__analysers = analysers

  def __call__(self, objects):
    results = self.Results(objects, self.__analysers)
    return Ens({name: getattr(results, name)
                for name in self.__analysers})


class Analysis(Analyser):
  @staticmethod
  def report(f):
    f._report = True
    return f

  def __init__(self):
    members = {name: getattr(self, name) for name in dir(self)}
    analysers = {name: f for name, f in members.items() if getattr(f, '_report', False)}
    super(Analysis, self).__init__(**analysers)