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
  """
  A class of read-only data structures emulating the initializer notation
  (literal notation) known from JavaScript.

  >>> deepThought = Ens(answer=42)

  Data stored in Ens object may be accessed both as its attributes, and as its
  items.

  >>> print(deepThought.answer)
  42
  >>> print(deepThought['answer'])
  42

  Not initialized attributes and items of Ens objects defaults to None.

  >>> print(deepThought.question)
  None
  >>> print(deepThought['question'])
  None

  It is possible to iterate for every attribute/key of the object.

  >>> for attr in deepThought:
  ...     print(attr)
  answer

  Objects can be initialized also with dict or Ens objects.

  >>> arthur = Ens(deepThought,
  ...              question='What do you get if you multiply six by nine?')
  >>> for attr in sorted(arthur):
  ...     print("{attr}: {val}".format(attr=attr, val=arthur[attr]))
  answer: 42
  question: What do you get if you multiply six by nine?
  >>> x = Ens(x=1)
  >>> y = Ens(y=2)
  >>> z = {'z': 3}
  >>> point = Ens(x, y, z)
  >>> print("Point at: {p.x}, {p.y}, {p.z}".format(p=point))
  Point at: 1, 2, 3

  The class has been designed to facilitate development of data analysis
  workflows with use of functional programming paradigm.
  """

  class ReadOnlyError(TypeError):
    """
    An error raised on attempt to modify an Ens object:
     - attribute assignment,
     - attribute deletion,
     - item assignment,
     - item deletion.
    """

  class AmbiguousInitializationError(ValueError):
    """
    An error raised in case if initialization of the object is ambiguous:
     - same attribute is present in many positional constructor arguments,
     - attribute present in positional argument(s) of the constructor is set
       also by its keyword argument.
    """

  def __init__(self, *dicts, **kwargs):
    for dict in (kwargs,) + dicts:
      for key in dict:
        Ens.__tryToSetAttribute(self.__dict__, key, dict[key])

  def __dict(self):
    return super(Ens, self).__getattribute__('__dict__')

  @classmethod
  def __tryToSetAttribute(cls, attributeDict, name, value):
    if name in attributeDict:
      raise cls.AmbiguousInitializationError

    if value is not None:
      attributeDict[name] = value

  def __getattribute__(self, name):
    if name == '__dict__':
      return super(Ens, self).__getattribute__(name)

    return self.__dict__.get(name)

  def __setattr__(self, name, value):
    raise Ens.ReadOnlyError

  def __delattr__(self, name):
    raise Ens.ReadOnlyError

  def __dir__(self):
    return list(self)
  
  def __iter__(self):
    return iter(self.__dict__)

  def __getitem__(self, key):
    return self.__dict__.get(key)

  def __setitem__(self, key, value):
    raise Ens.ReadOnlyError
  
  def __delitem__(self, key):
    raise Ens.ReadOnlyError

  @classmethod
  def map(cls, function, source, *otherSources):
    """
    Apply a function to every non None attribute (or item) of a source object.
    Construct an Ens object with attributes of same names, which values are
    results of the applied function.

    If multiple source objects are given, the function must accept that many
    positional arguments and is applied for every attribute which is non None
    for at least one source object. Subsequent arguments of the function are
    values of the attribute of corresponding source objects.

    :param function: the function to be applied
    :type function: callable

    :param source: the source object
    :type source: Ens or dict

    :param *otherSources: other source objects

    :return: the constructed object
    :rtype: Ens
    """
    return cls.__map(function, source, *otherSources)

  @classmethod
  def __map(cls, function, *sources):
    return cls.__mapForKeys(function, cls.__getAttrNames(*sources),
                            sources)

  @classmethod
  def __getAttrNames(cls, source, *otherSources):
    return frozenset(source).union(*otherSources)

  @classmethod
  def __mapForKeys(cls, function, keys, sources):
    return cls.__fromPairs((k, function(*[s[k] for s in sources]))
                           for k in keys)

  @classmethod
  def __fromPairs(cls, pairs):
    return cls(dict(pairs))