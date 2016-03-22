#!/usr/bin/env python
# encoding: utf-8
###############################################################################
#                                                                             #
#    PyMICE library                                                           #
#                                                                             #
#    Copyright (C) 2012-2016 Jakub M. Kowalski (Laboratory of                 #
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

class Ens(object):
  class ReadOnlyError(TypeError):
    pass

  class AmbiguousInitializationError(ValueError):
    pass

  def __init__(self, *dicts, **kwargs):
    for dict in (kwargs,) + dicts:
      for key in dict:
        Ens.__tryToSetAttribute(Ens.__dict(self), key, dict[key])

  def __dict(self):
    return super(Ens, self).__getattribute__('__dict__')

  @classmethod
  def __get(cls, ens, name):
    return cls.__dict(ens).get(name)

  @classmethod
  def __tryToSetAttribute(cls, attributeDict, name, value):
    if name in attributeDict:
      raise cls.AmbiguousInitializationError

    if value is not None:
      attributeDict[name] = value

  def __getattribute__(self, name):
    return Ens.__get(self, name)

  def __setattr__(self, name, value):
    raise Ens.ReadOnlyError

  def __delattr__(self, name):
    raise Ens.ReadOnlyError
  
  def __iter__(self):
    return iter(Ens.__dict(self))

  def __getitem__(self, key):
    return Ens.__get(self, key)

  def __setitem__(self, key, value):
    raise Ens.ReadOnlyError
  
  def __delitem__(self, key):
    raise Ens.ReadOnlyError

  @classmethod
  def map(cls, ens, f):
    return cls(dict((k, f(ens[k])) for k in ens))
