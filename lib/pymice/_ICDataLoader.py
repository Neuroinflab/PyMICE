#!/usr/bin/env python
# encoding: utf-8
###############################################################################
#                                                                             #
#    PyMICE library                                                           #
#                                                                             #
#    Copyright (C) 2012-2019 Jakub M. Dzik a.k.a. Kowalski, S. Łęski          #
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

import csv
from xml.dom import minidom

from .ICNodes import Animal

class _FileCollectionLoader(object):
  DATA_DESCRIPTOR_PATH = 'DataDescriptor.xml'

  def __init__(self, fileCollection):
    self._fileCollection = fileCollection

  @classmethod
  def canLoad(cls, fileCollection):
    return cls.version == cls._getVersion(fileCollection)

  @classmethod
  def _getVersion(cls, fileCollection):
    try:
      with fileCollection.open(cls.DATA_DESCRIPTOR_PATH) as fh:
        dom = minidom.parse(fh)

    except KeyError:
      return None

    dd = dom.getElementsByTagName('DataDescriptor')[0]
    versionNode = dd.getElementsByTagName('Version')[0]
    versionStr = versionNode.childNodes[0]
    assert versionStr.nodeType == versionStr.TEXT_NODE
    return versionStr.nodeValue.strip()

  @classmethod
  def getLoader(cls, fileCollection):
    for subclass in cls.__subclasses__():
      if subclass.canLoad(fileCollection):
        return subclass(fileCollection)

  def getMice(self):
    rows = list(csv.reader(self._fileCollection.open('Animals.txt'),
                           delimiter='\t'))
    return frozenset(Animal.fromRow(*row[:3]) for row in rows[1:])


class _FileCollectionLoader_v_Version1(_FileCollectionLoader):
  version = 'Version1'


class _FileCollectionLoader_v_Version_2_2(_FileCollectionLoader):
  version = 'Version_2_2'


class _FileCollectionLoader_v_IntelliCage_Plus_3(_FileCollectionLoader):
  version = 'IntelliCage_Plus_3'