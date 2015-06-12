#!/usr/bin/env python
# encoding: utf-8
###############################################################################
#                                                                             #
#    PyMICE library                                                           #
#                                                                             #
#    Copyright (C) 2012-2015 Jakub M. Kowalski, S. Łęski (Laboratory of       #
#    Neuroinformatics; Nencki Institute of Experimental Biology)              #
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

"""
pymice package

A collection of tools to access IntelliCage data.
"""

from .Data import Loader, Merger
from ._Tools import hTime, convertTime, getTutorialData
from ._Metadata import Phase, ExperimentConfigFile
from ._Results import ResultsCSV
from .LogAnalyser import LickometerLogAnalyzer, PresenceLogAnalyzer, TestMiceData
__ID__ = 'nlx_158570'
__version__ = __ID__ + ' 0.1.1'
__all__ = []

print "This is a bleeding edge version of the PyMICE library. It might meet your"
print "expectations, however it might also go to your fridge, drink all the beer"
print "it can found there and then eat your cat. Be warned."
print
