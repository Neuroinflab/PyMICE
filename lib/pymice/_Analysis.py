#!/usr/bin/env python
# encoding: utf-8
###############################################################################
#                                                                             #
#    PyMICE library                                                           #
#                                                                             #
#    Copyright (C) 2016-2017 Jakub M. Dzik a.k.a. Kowalski (Laboratory of     #
#    Neuroinformatics; Nencki Institute of Experimental Biology of Polish     #
#    Academy of Sciences)                                                     #
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
from ._Tools import groupBy
import sys

class Analyser(object):
  class Result(object):
    class CircularDependencyError(RuntimeError):
      pass

    class UnknownDependencyError(RuntimeError):
      pass

    class ReadOnlyError(TypeError):
      pass

    def __init__(self, data, analysers):
      self.__dict__['_data'] = data
      self.__dict__['_analysers'] = dict(analysers)
      self.__dict__['_lock'] = set()
      self.__dict__['_values'] = {}

    def __getattr__(self, name):
      try:
        return self._values[name]

      except KeyError:
        return self.__createAttribute(name)

    def __setattr__(self, key, value):
      raise self.ReadOnlyError

    def __createAttribute(self, name):
      self.__ensureNoPreviousAttemptsToCreate(name)
      return self.__calculateAndStoreAttribute(name)

    def __ensureNoPreviousAttemptsToCreate(self, item):
      if item in self._lock:
        raise self.CircularDependencyError

      self._lock.add(item)

    def __calculateAndStoreAttribute(self, name):
      analyser = self.__getAnalyser(name)
      value = self.__callAnalyser(analyser)
      self._values[name] = value
      return value

    def __getAnalyser(self, item):
      try:
        return self._analysers[item]

      except KeyError:
        raise self.UnknownDependencyError(item)

    def __callAnalyser(self, analyser):
      try:
        return analyser(self._data)

      except TypeError:
        if self.__exceptionNotInScope():
          raise

        return analyser(self, self._data)

    def __exceptionNotInScope(self):
      return sys.exc_info()[2].tb_next is not None

  def __init__(self, preprocessor=None, **analysers):
    if preprocessor is not None:
      self.preprocess = preprocessor

    self.__analysers = analysers

  def preprocess(self, data):
    return data

  def __call__(self, objects):
    results = self.Result(self.preprocess(objects),
                          self.__analysers)
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
    super(Analysis, self).__init__(None, **analysers)


class Aggregator(object):
  def __init__(self, getKey=lambda x: x, aggregateFunction=lambda x: x, requiredKeys=()):
    self.__getKey = getKey
    self.__requiredKeys = requiredKeys
    self.__aggregateFunction = aggregateFunction

  def __call__(self, sequence):
    aggregateFunction = self.__aggregateFunction
    getKey = self.__getKey
    requiredKeys = self.__requiredKeys
    return self.aggregate(sequence, getKey, aggregateFunction, requiredKeys)

  @staticmethod
  def aggregate(sequence, getKey=lambda x: x, aggregateFunction=lambda x: x, requiredKeys=()):
    return Ens.map(aggregateFunction,
                   groupBy(sequence,
                           getKey=getKey,
                           requiredKeys=requiredKeys))

  def __get__(self, instance, owner):
    return self.__class__(getKey=self.__getKeyForDescriptor(instance, owner),
                          requiredKeys=self.__requiredKeys,
                          aggregateFunction=self.__aggregateFunctionForDescriptor(instance, owner))

  def __aggregateFunctionForDescriptor(self, instance, owner):
    try:
      return self.__aggregateFunctionMethod.__get__(instance, owner)

    except AttributeError:
      return self.__aggregateFunction

  def __getKeyForDescriptor(self, instance, owner):
    try:
      return self.__getKeyMethod.__get__(instance, owner)

    except AttributeError:
      return self.__getKey

  def getKey(self, f):
    self.__getKeyMethod = f

  def aggregateFunction(self, f):
    self.__aggregateFunctionMethod = f


def histogram(values, bins):
  for a, b in zip(bins[:-1], bins[1:]):
    if a > b:
      raise ValueError

  result = [0] * (len(bins) - 1)
  for v in values:
    _insertElement(result, v, bins)
  return result


def _insertElement(result, element, bins):
  bottom = 0
  top = len(result)
  if bins[bottom] <= element < bins[top]:
    while top - bottom > 1:
      middle = (bottom + top) // 2
      if element < bins[middle]:
        top = middle
      else:
        bottom = middle

    result[bottom] += 1
  # for i, (bottom, top) in enumerate(zip(bins[:-1], bins[1:])):
  #   if bottom <= element < top:
  #     result[i] += 1
  #     break