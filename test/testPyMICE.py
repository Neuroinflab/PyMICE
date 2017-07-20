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
import sys

import unittest
from unittest import TestCase

import pymice as pm

if sys.version_info.major > 2:
    try:
        from importlib import reload
    except ImportError:
        from imp import reload


class CaptureSTDERR(object):
    def __enter__(self):
        self.__stderr = sys.stderr
        sys.stderr = self
        self.__captured = ''
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        sys.stderr = self.__stderr

    def write(self, string):
        self.__captured += string

    @property
    def CAPTURED(self):
        return self.__captured

class TestPyMICE(TestCase, CaptureSTDERR):
    TERMILNAL_LINE_WIDTH = 80

    def setUp(self):
        self.maxDiff = None

    def testImportMessageFitsTerminal(self):
        with CaptureSTDERR() as stderr:
            reload(pm)
            for line in stderr.CAPTURED.split('\n'):
                self.assertLessEqual(len(line), self.TERMILNAL_LINE_WIDTH)

    def testImportMessage(self):
        #self.maxDiff = None
        with CaptureSTDERR() as stderr:
            reload(pm)
            # the resource identifier (RRID:nlx_158570)
            self.assertEqual(u"""PyMICE library v. {version}

The library is available under GPL3 license; we ask that reference to our paper
as well as to the library itself is provided in any published research making
use of PyMICE.

The recommended in-text citation format is:
PyMICE\xa0(Dzik, Puścian, et\xa0al. 2017) v.\xa0{version}\xa0(Dzik, Łęski, &\xa0Puścian 2017)

and the recommended bibliography entry format:
Dzik\xa0J.\xa0M., Łęski\xa0S., Puścian\xa0A. (July\xa021,\xa02017) \"PyMICE\" computer software
    (v.\xa0{version}; RRID:nlx_158570) doi:\xa010.5281/zenodo.832982

Dzik\xa0J.\xa0M., Puścian\xa0A., Mijakowska\xa0Z., Radwanska\xa0K., Łęski\xa0S. (June\xa022,\xa02017)
    \"PyMICE: A Python library for analysis of IntelliCage data\" Behavior
    Research Methods doi:\xa010.3758/s13428-017-0907-5

If the journal does not allow for inclusion of the resource identifier
({rrid}) in the bibliography, we ask to provide it in-text:
PyMICE\xa0({rrid})\xa0[1] v.\xa0{version}\xa0[2]

1. Dzik\xa0JM, Puścian\xa0A, Mijakowska\xa0Z, Radwanska\xa0K, Łęski\xa0S. PyMICE: A Python
    library for analysis of IntelliCage data. Behav Res Methods. 2017.
    DOI:\xa010.3758/s13428-017-0907-5
2. Dzik\xa0JM, Łęski\xa0S, Puścian\xa0A. PyMICE [computer software]. Version {version}.
    Warsaw: Nencki Institute - PAS; 2017. DOI:\xa010.5281/zenodo.832982

We have provided a solution to facilitate referencing to the library. Please run

>>> help(pm.Citation)

for more information (given that the library is imported as `pm`).


""".format(version=pm.__version__, rrid=pm.__RRID__),
                            stderr.CAPTURED)
            for line in stderr.CAPTURED.split('\n'):
                self.assertLessEqual(len(line), self.TERMILNAL_LINE_WIDTH)

if __name__ == '__main__':
    unittest.main()