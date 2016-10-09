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

class Analysis(object):
  class Results(object):
    class CircularDependencyError(RuntimeError):
      pass

    class UnknownDependencyError(RuntimeError):
      pass

    class ObjectWrapper(tuple):
      def __new__(cls, seq, result):
        return tuple.__new__(cls, seq)

      def __init__(self, seq, result):
        self.result = result

    def __init__(self, objects, analysers):
      self.__objects = self.ObjectWrapper(objects, self)
      self.__analysers = dict(analysers)
      self.__lock = set()
      self.__values = {}

    def __getattr__(self, item):
      try:
        return self.__values[item]

      except KeyError:
        if item in self.__lock:
          raise self.CircularDependencyError

        self.__lock.add(item)
        try:
          value = self.__analysers[item](self.__objects)
        except KeyError:
          raise self.UnknownDependencyError

        self.__values[item] = value
        return value

    def __enter__(self):
      return self

    def __exit__(self, exc_type, exc_val, exc_tb):
      del self.__objects

  def __init__(self, **analysers):
    self.__analysers = analysers

  def __call__(self, objects):
    with self.Results(objects, self.__analysers) as results:
      return Ens({name: getattr(results, name)
                  for name in self.__analysers})