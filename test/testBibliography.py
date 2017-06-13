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
import unittest
import sys

import pymice as pm
from pymice._Bibliography import reference

class TestReference(unittest.TestCase):
    SOFTWARE = {
        'apa6': {'1.1.1': u"Dzik, J. M., Łęski, S., & Puścian, A. (2017, April). PyMICE (v. 1.1.1) [computer software; RRID:nlx_158570]. doi: 10.5281/zenodo.557087",
                 '1.1.0': u"Dzik, J. M., Łęski, S., & Puścian, A. (2016, December). PyMICE (v. 1.1.0) [computer software; RRID:nlx_158570]. doi: 10.5281/zenodo.200648",
                 '1.0.0': u"Dzik, J. M., Łęski, S., & Puścian, A. (2016, May). PyMICE (v. 1.0.0) [computer software; RRID:nlx_158570]. doi: 10.5281/zenodo.51092",
                 '0.2.5': u"Dzik, J. M., Łęski, S., & Puścian, A. (2016, April). PyMICE (v. 0.2.5) [computer software; RRID:nlx_158570]. doi: 10.5281/zenodo.49550",
                 '0.2.4': u"Dzik, J. M., Łęski, S., & Puścian, A. (2016, January). PyMICE (v. 0.2.4) [computer software; RRID:nlx_158570]. doi: 10.5281/zenodo.47305",
                 '0.2.3': u"Dzik, J. M., Łęski, S., & Puścian, A. (2016, January). PyMICE (v. 0.2.3) [computer software; RRID:nlx_158570]. doi: 10.5281/zenodo.47259",
                 'unknown': u"Dzik, J. M., Łęski, S., & Puścian, A. (n.d.). PyMICE (v. unknown) [computer software; RRID:nlx_158570]",
                 },
        'bibtex': {'1.1.1': u"pymice1.1.1{Title = {{PyMICE (v.~1.1.1)}}, Note = {computer software; RRID:nlx\\_158570}, Author = {Dzik, Jakub Mateusz and Łęski, Szymon and Puścian, Alicja}, Year = {2017}, Month = {April}, Doi = {10.5281/zenodo.557087}}",
                   '1.1.0': u"pymice1.1.0{Title = {{PyMICE (v.~1.1.0)}}, Note = {computer software; RRID:nlx\\_158570}, Author = {Dzik, Jakub Mateusz and Łęski, Szymon and Puścian, Alicja}, Year = {2016}, Month = {December}, Doi = {10.5281/zenodo.200648}}",
                   '1.0.0': u"pymice1.0.0{Title = {{PyMICE (v.~1.0.0)}}, Note = {computer software; RRID:nlx\\_158570}, Author = {Dzik, Jakub Mateusz and Łęski, Szymon and Puścian, Alicja}, Year = {2016}, Month = {May}, Doi = {10.5281/zenodo.51092}}",
                   '0.2.5': u"pymice0.2.5{Title = {{PyMICE (v.~0.2.5)}}, Note = {computer software; RRID:nlx\\_158570}, Author = {Dzik, Jakub Mateusz and Łęski, Szymon and Puścian, Alicja}, Year = {2016}, Month = {April}, Doi = {10.5281/zenodo.49550}}",
                   '0.2.4': u"pymice0.2.4{Title = {{PyMICE (v.~0.2.4)}}, Note = {computer software; RRID:nlx\\_158570}, Author = {Dzik, Jakub Mateusz and Łęski, Szymon and Puścian, Alicja}, Year = {2016}, Month = {January}, Doi = {10.5281/zenodo.47305}}",
                   '0.2.3': u"pymice0.2.3{Title = {{PyMICE (v.~0.2.3)}}, Note = {computer software; RRID:nlx\\_158570}, Author = {Dzik, Jakub Mateusz and Łęski, Szymon and Puścian, Alicja}, Year = {2016}, Month = {January}, Doi = {10.5281/zenodo.47259}}",
                   'unknown': u"pymiceunknown{Title = {{PyMICE (v.~unknown)}}, Note = {computer software; RRID:nlx\\_158570}, Author = {Dzik, Jakub Mateusz and Łęski, Szymon and Puścian, Alicja}}",
                   },
        'latex': {'1.1.1': u"\\emph{PyMICE} v.~1.1.1~\\cite{pymice1.1.1}",
                  },
    }

    def testSoftware(self):
        for style, tests in self.SOFTWARE.items():
            for version, expected in tests.items():
                self.checkUnicodeEqual(expected,
                                       reference.software(version, style))

    def testSoftwareCurrentVersionIsDefaultAPA6(self):
        self.checkUnicodeEqual(self.SOFTWARE['apa6'][pm.__version__],
                               reference.software(style='apa6'))

    def testSoftwareDefaultStyleIsAPA6(self):
        self.checkUnicodeEqual(self.SOFTWARE['apa6'][pm.__version__],
                               reference.software())

    def checkUnicodeEqual(self, expected, output):
        self.assertEqual(expected, output)
        self.assertIsInstance(output,
                              unicode if sys.version_info.major < 3 else str)

if __name__ == '__main__':
    unittest.main()