#!/usr/bin/env python
# encoding: utf-8
###############################################################################
#                                                                             #
#    PyMICE library                                                           #
#                                                                             #
#    Copyright (C) 2017 Jakub M. Dzik a.k.a. Kowalski (Laboratory of          #
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

class _ModuleDependencies(object):
  def __call__(self, *modules):
    dependencies = [self._dependencies(m) for m in modules]

    ambiguous = self._ambiguousVersions(dependencies)

    result = {n: (v, {dn: dd for dn, dd in ds.items() if dn in ambiguous}) for n, v, ds in dependencies}
    result.update((dn, dd)
                  for n, v, ds in dependencies
                  for dn, dd in ds.items() if dn not in ambiguous)
    return result

  def _ambiguousVersions(self, dependencies):
    return {k for k, v in self._versions(dependencies).items()
            if len(v) > 1}

  def _versions(self, dependencies):
    versions = {n: {v} for n, v, _ in dependencies}
    for _n, _v, d in dependencies:
      for dn, (dv, _) in d.items():
        try:
          versions[dn].add(dv)
        except KeyError:
          versions[dn] = {dv}
    return versions

  def _dependencies(self, module):
    return (self._getNameOrFail(module),
            getattr(module, '__version__', None),
            getattr(module, '__dependencies__', {}))

  def _getNameOrFail(self, module):
    try:
      return module.__name__
    except AttributeError:
      raise self.UnnamedModuleException

  class UnnamedModuleException(AttributeError):
    pass

moduleDependencies = _ModuleDependencies()
